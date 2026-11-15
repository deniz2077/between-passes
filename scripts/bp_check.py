"""Between Passes: run the weather filter on any place NISAR has flown.

    python scripts/bp_check.py --lat 42.00 --lon -93.60 [--name "Iowa, USA"] [--out results/iowa]

1. Finds the two most recent VALIDATED NISAR L2 GCOV passes over the point from the same
   track, direction and frame (NASA CMR), so the pixels line up with no resampling.
2. Reads only a 10 x 10 km window of each file over HTTP (needs your own free NASA
   Earthdata Login in ~/.netrc; scripts/setup_earthdata_netrc.py sets it up).
3. Reads NASA SMAP soil moisture (SPL3SMP_E) for both days and NASA POWER rain in between.
4. Applies the fixed filter rules (research/filter/WEATHER_FILTER.md) and writes before/after
   images, the filtered change map, report.json and report.md.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(__file__))
import global_scan as gs  # noqa: E402  (NISAR window reader, EASE grid, SMAP cell reader)
from bp_science import boxcar_linear  # noqa: E402
from build_sites import classify, render, FIT  # noqa: E402

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
RX = re.compile(r"NISAR_L2_PR_GCOV_(\d{3})_(\d{3})_([AD])_(\d{3})_\d{4}_(\w{4})_A_(\d{8}T\d{6})_\d{8}T\d{6}_(P\d{5})_")


def find_pair(lon, lat):
    r = requests.get(CMR, params=dict(short_name="NISAR_L2_GCOV_V1", point=f"{lon},{lat}", page_size=500), timeout=60)
    r.raise_for_status()
    groups = {}
    for e in r.json()["feed"]["entry"]:
        m = RX.match(e["title"])
        if not m or m.group(5) not in ("DHDH", "SHSH", "QPDH"):
            continue
        key = (m.group(2), m.group(3), m.group(4), m.group(7))
        groups.setdefault(key, {})[m.group(6)[:8]] = e["title"]
    pairs = []
    for key, by_date in groups.items():
        d = sorted(by_date)
        if len(d) >= 2:
            pairs.append((d[-1], d[-2], key, by_date[d[-2]], by_date[d[-1]]))
    if not pairs:
        raise SystemExit("No repeat NISAR pass over this point in CMR yet (needs two passes on the same track and frame).")
    pairs.sort(reverse=True)  # most recent second pass first
    return [(key, a, b) for _, _, key, a, b in pairs]


def smap_value(lon, lat, date, local_hour):
    """Pre-registered SMAP rule: overpass nearest the NISAR local time, recommended quality, then +/-1 day."""
    r_, c_ = gs.ease_rc(lon, lat)
    want = "AM" if abs(local_hour - 6) <= abs(local_hour - 18) else "PM"
    order = [(0, want), (0, "PM" if want == "AM" else "AM"), (-1, want), (1, want), (-1, "PM" if want == "AM" else "AM"), (1, "PM" if want == "AM" else "AM")]
    cache = {}
    for dd, ov in order:
        day = (datetime.strptime(date, "%Y%m%d") + timedelta(days=dd)).strftime("%Y%m%d")
        if day not in cache:
            q = requests.get(CMR, params=dict(short_name="SPL3SMP_E", temporal=f"{day[:4]}-{day[4:6]}-{day[6:]}T00:00:00Z,{day[:4]}-{day[4:6]}-{day[6:]}T23:59:59Z", page_size=20), timeout=60).json()["feed"]["entry"]
            urls = sorted(l["href"] for e in q for l in e["links"] if l["href"].endswith(".h5") and l["href"].startswith("https"))
            cache[day] = {}
            for attempt in range(3):  # NASA servers occasionally answer 502; retry, never hide a failure
                try:
                    cache[day] = gs.smap_day((day, urls[-1], [(r_, c_)]))[1] if urls else {}
                    break
                except Exception as e:
                    print(f"  SMAP {day}: {type(e).__name__}, retry {attempt + 1}/3")
        v = cache[day].get(f"{r_},{c_},{ov}")
        if v and (v[1] & 1) == 0 and 0 <= v[0] <= 0.6:
            return dict(value=round(v[0], 4), day=day, overpass=ov)
    return None


def power_rain(lon, lat, a, b):
    r = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point", timeout=120,
                     params=dict(parameters="PRECTOTCORR", community="AG", longitude=lon, latitude=lat, start=a, end=b, format="JSON"))
    try:
        s = r.json()["properties"]["parameter"]["PRECTOTCORR"]
        return round(sum(v for k, v in s.items() if a < k <= b and v >= 0), 2)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    name = a.name or f"{a.lat:.2f}, {a.lon:.2f}"
    out = a.out or os.path.join("results", re.sub(r"\W+", "_", name).strip("_").lower())
    os.makedirs(out, exist_ok=True)

    for key, ga, gb in find_pair(a.lon, a.lat)[:3]:  # most recent pair whose window is at least half valid
        da, db = RX.match(ga).group(6), RX.match(gb).group(6)
        print(f"NISAR pair: track {key[0]} {key[1]} frame {key[2]}  {da[:8]} -> {db[:8]}")
        A, B = gs._read(ga, a.lon, a.lat), gs._read(gb, a.lon, a.lat)
        if A["hh"].shape != B["hh"].shape or not np.array_equal(A["x"], B["x"]) or A["hh"].size == 0:
            print("  grids differ or window empty; trying the next pair"); continue
        va = (A["mask"] >= 1) & (A["mask"] <= 254) & np.isfinite(A["hh"]) & (A["hh"] > 0)
        vb = (B["mask"] >= 1) & (B["mask"] <= 254) & np.isfinite(B["hh"]) & (B["hh"] > 0)
        if A["exc"] is not None: va &= A["exc"] == 768
        if B["exc"] is not None: vb &= B["exc"] == 768
        v = va & vb
        spacing = float(abs(A["x"][1] - A["x"][0]))
        frac = v.sum() / round(2 * gs.HALF_M / spacing) ** 2
        if frac >= 0.5:
            break
        print(f"  only {frac:.0%} of the window is valid on both dates; trying the next pair")
    else:
        raise SystemExit("No NISAR pair with at least half of the 10 km window valid here. Try a point further inside a swath.")
    la, lb = np.where(v, A["hh"], 0).astype(np.float64), np.where(v, B["hh"], 0).astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = 10 * np.log10(boxcar_linear(lb, v, 5) / boxcar_linear(la, v, 5))
    utc = datetime.strptime(da, "%Y%m%dT%H%M%S")
    local = (utc.hour + utc.minute / 60 + a.lon / 15) % 24
    print("SMAP soil moisture…")
    sa, sb = smap_value(a.lon, a.lat, da[:8], local), smap_value(a.lon, a.lat, db[:8], local)
    if not (sa and sb):
        raise SystemExit("No quality-approved SMAP soil moisture within a day of both passes here, so the filter cannot run (same rule as the worldwide test).")
    dsm = sb["value"] - sa["value"]
    rain = power_rain(a.lon, a.lat, da[:8], db[:8])
    r, w, bb = classify(d, v & np.isfinite(d), dsm)
    render(out, la, lb, v, w, bb, max(1, int(round(20 / spacing))))
    dhh = float(10 * np.log10(lb[v].mean() / la[v].mean()))
    rep = dict(name=name, lon=a.lon, lat=a.lat, granule_a=ga, granule_b=gb, date_a=da[:8], date_b=db[:8], spacing_m=spacing,
               valid_frac=round(float(frac), 3), local_hour=round(local, 2), smap_a=sa, smap_b=sb, sm_a=sa["value"], sm_b=sb["value"], dSM=round(dsm, 4),
               rain_mm=rain, dHH_db=round(dhh, 3), expected_dHH_db=round(FIT[0] * dsm * 10 + FIT[1], 3), **r,
               rules="research/filter/WEATHER_FILTER.md", generated_utc=datetime.utcnow().isoformat(timespec="seconds") + "Z")
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1)
    V = {"weather": "Mostly the weather", "beyond": "Real change beyond the weather", "quiet": "Quiet: little changed"}[r["verdict"]]
    md = f"""# Between Passes · {name}

**{V}**

- NISAR passes: {da[:8]} → {db[:8]} (track {key[0]} {key[1]}, frame {key[2]}, {spacing:.0f} m pixels, {frac:.0%} valid)
- Soil moisture (NASA SMAP): {sa['value']:.3f} → {sb['value']:.3f} m³/m³ (soil {r['soil']})
- Rain between passes (NASA POWER): {rain} mm
- Land that changed ≥ 3 dB: {100 * r['changed_frac']:.1f}%  ·  could be the weather: {100 * r['weather_frac']:.1f}%  ·  beyond the weather: {100 * r['beyond_frac']:.1f}%
- Radar change, whole window: {dhh:+.2f} dB (soil moisture alone predicts {rep['expected_dHH_db']:+.2f} dB)

Images: before.jpg, after.jpg, filter.png (blue = could be the weather, amber = beyond the weather).
Granules: {ga} / {gb}
"""
    open(os.path.join(out, "report.md"), "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
