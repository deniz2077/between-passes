"""Global test (pre-registered in research/global/PREREGISTRATION.md).

Step 1  sample   : draw the 200-pair random sample (seed 2026) -> research/global/sample.json
Step 2  nisar    : per pair, read a 10 km HH window from both granules (HTTP range reads),
                   compute site metrics + a 100 m dHH thumbnail -> research/global/sites/<k>.json/.npy
Step 3  smap     : SMAP L3 Enhanced soil moisture at every site/date -> research/global/smap.json
Step 4  power    : NASA POWER daily rain at every site -> research/global/power.json

Usage: python scripts/global_scan.py sample|nisar|smap|power [workers]
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
G = os.path.join(ROOT, "research", "global")
SET = os.environ.get("BP_SET", "")  # "" = original sample, "rep" = pre-registered replication
SFX = "_" + SET if SET else ""
SITES = os.path.join(G, "sites" + SFX)
HH_MODES = ("DHDH", "SHSH", "QPDH")
N_SAMPLE = 200
SEED = 2027 if SET == "rep" else 2026
HALF_M = 5000.0


# ---------------------------------------------------------------- step 1
def make_sample():
    recs = json.load(open(os.path.join(G, "cmr_gcov_all.json")))
    groups = defaultdict(list)
    for r in recs:
        if r["pol"] in HH_MODES:
            groups[(r["track"], r["dir"], r["frame"], r["crid"], r["pol"])].append(r)
    pairs = []
    for key in sorted(groups):
        v = groups[key]
        dates = sorted(set(x["date"] for x in v))
        if len(dates) < 2:
            continue
        a = sorted([x for x in v if x["date"] == dates[0]], key=lambda x: x["gid"])[-1]
        b = sorted([x for x in v if x["date"] == dates[-1]], key=lambda x: x["gid"])[-1]
        pairs.append(dict(key="_".join(key), a=a["gid"], b=b["gid"], date_a=a["date"],
                          date_b=b["date"], lon=a["lon"], lat=a["lat"], mode=a["pol"]))
    n_all = len(pairs)
    elig = [p for p in pairs if abs(p["lat"]) <= 60]
    if SET == "rep":  # exclude every pair used by the original sample
        used = {x["key"] for x in json.load(open(os.path.join(G, "sample.json")))["sample"]}
        elig = [p for p in elig if p["key"] not in used]
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(elig), size=N_SAMPLE, replace=False).tolist())
    sample = [dict(k=i, **elig[j]) for i, j in enumerate(idx)]
    json.dump(dict(n_pairs=n_all, n_eligible=len(elig), seed=SEED, sample=sample),
              open(os.path.join(G, f"sample{SFX}.json"), "w"), indent=1)
    print("pairs", n_all, "eligible", len(elig), "sampled", len(sample))


# ---------------------------------------------------------------- step 2
def _read(gid, lon, lat):
    import h5py
    from rasterio.warp import transform as wt
    from nisar_remote import RemoteFile, granule_url
    rf = RemoteFile(granule_url(gid))
    with h5py.File(rf, "r") as f:
        g = f["/science/LSAR/GCOV/grids/frequencyA"]
        epsg = int(g["projection"][()])
        x = g["xCoordinates"][:]
        y = g["yCoordinates"][:]
        xs, ys = wt("EPSG:4326", f"EPSG:{epsg}", [lon], [lat])
        cx, cy = xs[0], ys[0]
        c0, c1 = int(np.searchsorted(x, cx - HALF_M)), int(np.searchsorted(x, cx + HALF_M))
        r0, r1 = int(np.searchsorted(-y, -(cy + HALF_M))), int(np.searchsorted(-y, -(cy - HALF_M)))
        out = dict(epsg=epsg, x=x[c0:c1].copy(), y=y[r0:r1].copy(),
                   hh=g["HHHH"][r0:r1, c0:c1], mask=g["mask"][r0:r1, c0:c1],
                   exc=(g["inputDataExceptionMask"][r0:r1, c0:c1]
                        if "inputDataExceptionMask" in g else None),
                   bytes=rf.bytes_fetched)
    return out


def _utc(gid):
    m = re.search(r"_A_(\d{8}T\d{6})_", gid)
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")


def site_job(p):
    from bp_science import boxcar_linear, block_mean_linear, encode_db_int16
    k = p["k"]
    out_json = os.path.join(SITES, f"{k:03d}.json")
    if os.path.exists(out_json):
        return k, "cached"
    res = dict(p)
    t0 = time.time()
    try:
        A = _read(p["a"], p["lon"], p["lat"])
        B = _read(p["b"], p["lon"], p["lat"])
    except Exception as e:  # network / format problems are recorded, not hidden
        res.update(status="drop", reason=f"read error: {type(e).__name__}: {e}"[:300])
        json.dump(res, open(out_json, "w"), indent=1)
        return k, res["reason"]
    res["bytes"] = int(A["bytes"] + B["bytes"])
    res["epsg"] = A["epsg"]
    utc = _utc(p["a"])
    res["local_solar_hour"] = round((utc.hour + utc.minute / 60 + p["lon"] / 15) % 24, 2)
    if (A["epsg"] != B["epsg"] or A["hh"].shape != B["hh"].shape or A["hh"].size == 0
            or not np.array_equal(A["x"], B["x"]) or not np.array_equal(A["y"], B["y"])):
        res.update(status="drop", reason="grids differ or window empty")
        json.dump(res, open(out_json, "w"), indent=1)
        return k, res["reason"]
    va = (A["mask"] >= 1) & (A["mask"] <= 254) & np.isfinite(A["hh"]) & (A["hh"] > 0)
    vb = (B["mask"] >= 1) & (B["mask"] <= 254) & np.isfinite(B["hh"]) & (B["hh"] > 0)
    if A["exc"] is not None:
        va &= A["exc"] == 768
    if B["exc"] is not None:
        vb &= B["exc"] == 768
    v = va & vb
    dx = float(abs(A["x"][1] - A["x"][0]))
    res["spacing_m"] = dx
    nominal = int(round(2 * HALF_M / dx) ** 2)
    res["valid_frac"] = round(float(v.sum()) / nominal, 4)
    res["exc_values_a"] = (np.unique(A["exc"])[:10].tolist() if A["exc"] is not None else None)
    if res["valid_frac"] < 0.5:
        res.update(status="drop", reason="valid fraction < 0.5")
        json.dump(res, open(out_json, "w"), indent=1)
        return k, res["reason"]
    hha = np.where(v, A["hh"], np.nan).astype(np.float64)
    hhb = np.where(v, B["hh"], np.nan).astype(np.float64)
    res["dHH_site_db"] = round(float(10 * np.log10(np.nanmean(hhb) / np.nanmean(hha))), 4)
    res["HH_a_site_db"] = round(float(10 * np.log10(np.nanmean(hha))), 3)
    res["HH_b_site_db"] = round(float(10 * np.log10(np.nanmean(hhb))), 3)
    sa, sb = boxcar_linear(np.nan_to_num(hha), v, 5), boxcar_linear(np.nan_to_num(hhb), v, 5)
    d = 10 * np.log10(sb / sa)
    dv = d[v & np.isfinite(d)]
    res["frac_up3"] = round(float((dv >= 3).mean()), 4)
    res["frac_dn3"] = round(float((dv <= -3).mean()), 4)
    res["net_frac3"] = round(res["frac_up3"] - res["frac_dn3"], 4)
    res["dHH_px_median_db"] = round(float(np.median(dv)), 4)
    # 100 m thumbnail of dHH (ratio of block-mean linear power), int16 dB*100
    ba, bb = block_mean_linear(np.nan_to_num(hha), v, 5), block_mean_linear(np.nan_to_num(hhb), v, 5)
    thumb = encode_db_int16(10 * np.log10(bb / ba))
    np.save(os.path.join(SITES, f"{k:03d}_dhh100.npy"), thumb)
    res["thumb_shape"] = list(thumb.shape)
    res.update(status="ok", seconds=round(time.time() - t0, 1))
    json.dump(res, open(out_json, "w"), indent=1)
    return k, f"ok dHH={res['dHH_site_db']:+.2f} dB valid={res['valid_frac']:.2f}"


def run_nisar(workers):
    os.makedirs(SITES, exist_ok=True)
    sample = json.load(open(os.path.join(G, "sample.json")))["sample"]
    with Pool(workers) as pool:
        for k, msg in pool.imap_unordered(site_job, sample):
            print(f"{k:03d} {msg}", flush=True)


# ---------------------------------------------------------------- step 3
EASE = dict(cell=9008.055210146, x0=-17367530.44516138, y0=7314540.83051517, ncol=3856, nrow=1624)


def ease_rc(lon, lat):
    from rasterio.warp import transform as wt
    xs, ys = wt("EPSG:4326", "EPSG:6933", [lon], [lat])
    c = int((xs[0] - EASE["x0"]) // EASE["cell"])
    r = int((EASE["y0"] - ys[0]) // EASE["cell"])
    return r, c


def smap_day(args):
    import h5py
    from nisar_remote import RemoteFile
    date, url, cells = args
    out = {}
    rf = RemoteFile(url)
    with h5py.File(rf, "r") as f:
        for ov, grp, sfx in (("AM", "Soil_Moisture_Retrieval_Data_AM", ""),
                             ("PM", "Soil_Moisture_Retrieval_Data_PM", "_pm")):
            g = f[grp]
            sm, qf = g["soil_moisture" + sfx], g["retrieval_qual_flag" + sfx]
            lat, lon = g["latitude" + sfx], g["longitude" + sfx]
            for (r, c) in cells:
                out[f"{r},{c},{ov}"] = [float(sm[r, c]), int(qf[r, c]), float(lat[r, c]), float(lon[r, c])]
    return date, out


def run_smap(workers):
    sample = json.load(open(os.path.join(G, "sample.json")))["sample"]
    extra = [dict(k="ceyhan", lon=35.85, lat=37.0)]
    cells = {}
    for p in sample + extra:
        cells[str(p["k"])] = ease_rc(p["lon"], p["lat"])
    urls = {}
    for gid, url in json.load(open(os.path.join(G, "smap_l3e_urls.json"))):
        d = gid[15:23]
        if url and (d not in urls or url > urls[d]):  # latest file version per day
            urls[d] = url
    uniq = sorted(set(cells.values()))
    jobs = [(d, urls[d], uniq) for d in sorted(urls) if "20261019" <= d <= "20261112"]
    cache = os.path.join(G, "smap_days" + SFX)
    os.makedirs(cache, exist_ok=True)
    days = {}
    for d, _, _ in jobs:
        fn = os.path.join(cache, f"{d}.json")
        if os.path.exists(fn):
            days[d] = json.load(open(fn))
    todo = [j for j in jobs if j[0] not in days]
    with Pool(workers) as pool:
        for d, out in pool.imap_unordered(smap_day, todo):
            days[d] = out
            json.dump(out, open(os.path.join(cache, f"{d}.json"), "w"))
            print("smap", d, flush=True)
    json.dump(dict(cells=cells, files={d: urls[d] for d in days}, days=days),
              open(os.path.join(G, f"smap{SFX}.json"), "w"))


# ---------------------------------------------------------------- step 4
def run_power(_workers):
    import requests
    sample = json.load(open(os.path.join(G, "sample.json")))["sample"]
    pts = [(str(p["k"]), p["lon"], p["lat"]) for p in sample] + [("ceyhan", 35.8, 37.0)]
    path = os.path.join(G, f"power{SFX}.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    for k, lon, lat in pts:
        if k in out:
            continue
        r = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point",
                         params=dict(parameters="PRECTOTCORR", community="AG", longitude=lon,
                                     latitude=lat, start="20261015", end="20261112", format="JSON"),
                         timeout=120)
        try:
            out[k] = r.json()["properties"]["parameter"]["PRECTOTCORR"]
        except Exception:
            out[k] = None
        json.dump(out, open(path, "w"))
        print("power", k, flush=True)


if __name__ == "__main__":
    step = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    {"sample": lambda: make_sample(), "nisar": lambda: run_nisar(w),
     "smap": lambda: run_smap(w), "power": lambda: run_power(w)}[step]()
