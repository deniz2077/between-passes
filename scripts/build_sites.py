"""Apply the weather filter (research/filter/WEATHER_FILTER.md, rules committed before this ran)
to every retained worldwide-test site, and export site cards for the app.

Inputs : research/global/results*.json (site metrics, SMAP, POWER), data/raw/sites/<key>.npz
         (from scripts/fetch_site_windows.py), app/data/ceyhan/ (Ceyhan, exploratory SMAP).
Outputs: app/data/sites/sites.json, app/data/sites/<id>/{before.jpg,after.jpg,filter.png}
         research/filter/results.json (summary).
"""
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from bp_science import boxcar_linear, block_mean_linear  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "sites")
OUT = os.path.join(ROOT, "app", "data", "sites")
WEATHER = (111, 168, 220)
BEYOND = (255, 176, 32)
# rules (fixed in WEATHER_FILTER.md)
SM_T, DB_T, QUIET, SHARE = 0.05, 3.0, 0.01, 2 / 3
FIT = (1.023, -0.134)  # dB per 0.1 m3/m3, intercept (pre-registered original sample)


def classify(d, an, dsm):
    up, dn = (d >= DB_T) & an, (d <= -DB_T) & an
    soil = "wetter" if dsm >= SM_T else "drier" if dsm <= -SM_T else "steady"
    if soil == "wetter":
        w, b = up, dn
    elif soil == "drier":
        w, b = dn, up
    else:
        w, b = np.zeros_like(up), up | dn
    nv = int(an.sum())
    nw, nb = int(w.sum()), int(b.sum())
    changed = (nw + nb) / nv
    if changed < QUIET:
        verdict = "quiet"
    elif soil != "steady" and nw / (nw + nb) >= SHARE:
        verdict = "weather"
    else:
        verdict = "beyond"
    return dict(soil=soil, valid_px=nv, changed_frac=round(changed, 4), weather_frac=round(nw / nv, 4),
                beyond_frac=round(nb / nv, 4), weather_share=round(nw / (nw + nb), 3) if nw + nb else None,
                verdict=verdict), w, b


def gray(lin):
    db = 10 * np.log10(np.maximum(lin, 1e-6))
    return (np.clip((db + 22) / 22, 0, 1) ** 0.9 * 255).astype(np.uint8)


def render(folder, la, lb, valid, w, b, f):
    os.makedirs(folder, exist_ok=True)
    if f > 1:
        ga, gb = block_mean_linear(la, valid, f), block_mean_linear(lb, valid, f)
        H, W = ga.shape
        ww = w[:H * f, :W * f].reshape(H, f, W, f).mean((1, 3)) >= 0.5
        bb = b[:H * f, :W * f].reshape(H, f, W, f).mean((1, 3)) >= 0.5
        vv = valid[:H * f, :W * f].reshape(H, f, W, f).mean((1, 3)) >= 0.5
    else:
        ga, gb, ww, bb, vv = boxcar_linear(la, valid, 3), boxcar_linear(lb, valid, 3), w, b, valid
    for name, g in (("before.jpg", ga), ("after.jpg", gb)):
        img = np.where(vv, gray(np.nan_to_num(g)), 0).astype(np.uint8)
        Image.fromarray(img).save(os.path.join(folder, name), quality=84)
    rgba = np.zeros(ww.shape + (4,), np.uint8)
    rgba[ww] = (*WEATHER, 235)
    rgba[bb] = (*BEYOND, 255)
    Image.fromarray(rgba).save(os.path.join(folder, "filter.png"), optimize=True)


def site(s, set_name):
    z = np.load(os.path.join(RAW, s["key"] + ".npz"))
    la, lb, v = z["hh_a"].astype(np.float64), z["hh_b"].astype(np.float64), z["valid"]
    sa, sb = boxcar_linear(la, v, 5), boxcar_linear(lb, v, 5)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = 10 * np.log10(sb / sa)
    an = v & np.isfinite(d)
    r, w, b = classify(d, an, s["dSM"])
    sid = s["key"].split("_P0")[0].lower()
    f = max(1, int(round(20 / float(z["spacing"]))))
    render(os.path.join(OUT, sid), la, lb, v, w, b, f)
    return dict(id=sid, set=set_name, lon=s["lon"], lat=s["lat"], date_a=s["date_a"], date_b=s["date_b"],
                granule_a=s["a"], granule_b=s["b"], spacing_m=float(z["spacing"]), local_hour=s["local_solar_hour"],
                dHH_db=s["dHH_site_db"], HH_a_db=s["HH_a_site_db"], HH_b_db=s["HH_b_site_db"],
                sm_a=s["sm_a"], sm_b=s["sm_b"], dSM=s["dSM"], rain_mm=s.get("rain", {}).get("between"),
                expected_dHH_db=round(FIT[0] * s["dSM"] * 10 + FIT[1], 3), **r)


def ceyhan():
    CE = os.path.join(ROOT, "app", "data", "ceyhan")
    C = json.load(open(os.path.join(CE, "case.json")))
    G = json.load(open(os.path.join(ROOT, "app", "data", "global", "global.json")))
    ex = G["ceyhan"]["exploratory"]
    a = np.fromfile(os.path.join(CE, "hh_a.i16"), np.int16).reshape(1200, 1200)
    b = np.fromfile(os.path.join(CE, "hh_b.i16"), np.int16).reshape(1200, 1200)
    fl = np.fromfile(os.path.join(CE, "flags.u8"), np.uint8).reshape(1200, 1200)
    v = (fl & 1).astype(bool)
    la, lb = np.where(v, 10 ** (a / 1000.0), 0), np.where(v, 10 ** (b / 1000.0), 0)
    d = 10 * np.log10(boxcar_linear(lb, v, 5) / boxcar_linear(la, v, 5))
    an = (fl & 2).astype(bool)
    r, w, bb = classify(d, an, ex["dSM"])
    sl = (slice(500, 1180), slice(310, 1190))
    render(os.path.join(OUT, "ceyhan"), la[sl], lb[sl], v[sl], w[sl], bb[sl], 1)
    rain = sum(x["mm"] for x in C["weather"]["series"] if "20261022" < x["date"] <= "20261103")
    st = C["stats"]["analysis_area"]
    return dict(id="ceyhan", set="case", name="Ceyhan, Türkiye", lon=35.85, lat=37.0, date_a="20261022", date_b="20261103",
                granule_a=C["acquisitions"]["a"]["granule"], granule_b=C["acquisitions"]["b"]["granule"], spacing_m=20.0,
                local_hour=19.4, dHH_db=round(st["dHH_db_region"], 3), sm_a=ex["sm_a"], sm_b=ex["sm_b"], dSM=ex["dSM"],
                rain_mm=round(rain, 2), expected_dHH_db=round(FIT[0] * ex["dSM"] * 10 + FIT[1], 3), exploratory_smap=True, **r)


def countries():
    """Natural Earth 1:50m admin-0 (public domain) via world-atlas@2.0.2 TopoJSON."""
    from shapely.geometry import Polygon, MultiPolygon
    T = json.load(open(os.path.join(ROOT, "data", "context", "ne", "countries-50m.json")))
    sc, tr = T["transform"]["scale"], T["transform"]["translate"]
    arcs = []
    for a in T["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)

    def ring(ix):
        pts = []
        for i in ix:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        return pts
    out = []
    for g in T["objects"]["countries"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        shp = MultiPolygon([Polygon(ring(p[0]), [ring(h) for h in p[1:]]) for p in polys]).buffer(0)
        out.append((g["properties"]["name"], shp))
    return out


def name_for(C, lon, lat):
    from shapely.geometry import Point
    p = Point(lon, lat)
    best = min(C, key=lambda c: c[1].distance(p))
    return best[0] if best[1].distance(p) < 0.5 else "open water / coast"


def main():
    os.makedirs(OUT, exist_ok=True)
    sites = []
    for f, name in (("results.json", "original"), ("results_rep.json", "replication")):
        for s in json.load(open(os.path.join(ROOT, "research", "global", f)))["sites"]:
            sites.append(site(s, name))
    sites.append(ceyhan())
    C = countries()
    for x in sites:
        x.setdefault("name", name_for(C, x["lon"], x["lat"]))
    cnt = {k: sum(1 for s in sites if s["verdict"] == k and s["id"] != "ceyhan") for k in ("weather", "beyond", "quiet")}
    soil = [s for s in sites if s["id"] != "ceyhan"]
    moved = [s["changed_frac"] for s in soil if s["soil"] != "steady"]
    still = [s["changed_frac"] for s in soil if abs(s["dSM"]) <= 0.02]
    # how much changed land, pooled over sites where soil moisture moved, the filter attributes to weather
    tw = sum(s["weather_frac"] * s["valid_px"] for s in soil if s["soil"] != "steady")
    tb = sum(s["beyond_frac"] * s["valid_px"] for s in soil if s["soil"] != "steady")
    summary = dict(n_sites=len(soil), verdicts=cnt, rules="research/filter/WEATHER_FILTER.md",
                   soil_moved_n=len(moved), soil_steady_n=len(still),
                   median_changed_frac_soil_moved=round(float(np.median(moved)), 4),
                   median_changed_frac_soil_steady=round(float(np.median(still)), 4),
                   ratio=round(float(np.median(moved) / np.median(still)), 1),
                   pooled_weather_share_where_soil_moved=round(tw / (tw + tb), 3),
                   ceyhan={k: sites[-1][k] for k in ("verdict", "weather_share", "changed_frac", "soil")})
    blob = json.dumps(dict(summary=summary, sites=sites), separators=(",", ":"))
    open(os.path.join(OUT, "sites.json"), "w").write(blob)
    summary["sha256_sites_json"] = hashlib.sha256(blob.encode()).hexdigest()
    json.dump(summary, open(os.path.join(ROOT, "research", "filter", "results.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
