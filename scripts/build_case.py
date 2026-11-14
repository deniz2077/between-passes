"""Build the frozen Between Passes case dataset for the web app.

Inputs : data/raw/win_A/{20261022,20261103}_A_*.tif   (from extract_window.py)
         data/context/power_*.json, data/context/osm_context_raw.json
Outputs: app/data/ceyhan/  (binary layers + case.json)

Run:  .venv/bin/python scripts/build_case.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.warp import transform as warp
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
import bp_science as bp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data/raw/win_A")
OUT = os.path.join(ROOT, "app/data/ceyhan")
DATES = {"a": "20261022", "b": "20261103"}
GRANULES = {
    "a": "NISAR_L2_PR_GCOV_033_151_D_070_2005_DHDH_A_20261022T162402_20261022T162437_P05036_N_F_J_001",
    "b": "NISAR_L2_PR_GCOV_034_151_D_070_2005_DHDH_A_20261103T162403_20261103T162437_P05036_N_F_J_001",
}
PARAMS = {
    "speckle_boxcar_px": 5,          # 100 m x 100 m window on linear gamma0
    "edge_buffer_px": 25,            # 500 m from invalid/out-of-swath pixels
    "object_core_db": 3.0,           # |ΔHH| seed (factor 2 in power)
    "object_grow_db": 2.0,           # hysteresis growth
    "object_min_px": 25,             # 1 ha at 20 m posting
    "urban_threshold_db": 0.0,       # HH > 0 dB on both dates (smoothed)
    "field_like_max_db": -5.0,       # HH < -5 dB on both dates (smoothed)
    "hv_block_px": 2,                # HV shipped at 40 m
    "lonlat_grid_step_px": 40,
    "optical_min_clear_frac": 0.8,   # object needs >= 80% pixels clear on both HLS dates
    "ndvi_change": 0.10,             # |dNDVI| threshold for vegetation loss / greening
}


def rd(date, layer):
    with rasterio.open(os.path.join(RAW, f"{date}_A_{layer}.tif")) as s:
        return s.read(1), s.transform, s.crs


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    L = {}
    for k, d in DATES.items():
        for layer in ("HHHH", "HVHV", "mask", "inputDataExceptionMask"):
            L[k, layer], T, crs = rd(d, layer)
    H, W = L["a", "HHHH"].shape
    epsg = crs.to_epsg()

    valid = bp.joint_valid(L["a", "HHHH"], L["b", "HHHH"], L["a", "HVHV"], L["b", "HVHV"],
                           L["a", "mask"], L["b", "mask"], L["a", "inputDataExceptionMask"],
                           L["b", "inputDataExceptionMask"])
    analysis = bp.edge_buffer(valid, PARAMS["edge_buffer_px"])
    k = PARAMS["speckle_boxcar_px"]
    hh = {s: L[s, "HHHH"].astype("float64") for s in "ab"}
    hv = {s: L[s, "HVHV"].astype("float64") for s in "ab"}
    hh_s = {s: bp.boxcar_linear(hh[s], analysis, k) for s in "ab"}
    d_hh = bp.to_db(hh_s["b"]) - bp.to_db(hh_s["a"])
    hh_db_s = {s: bp.to_db(hh_s[s]) for s in "ab"}

    # Stable urban control: largest connected persistently-bright cluster
    bright = analysis & (hh_db_s["a"] > PARAMS["urban_threshold_db"]) & \
        (hh_db_s["b"] > PARAMS["urban_threshold_db"])
    lab, n = ndimage.label(bright, structure=np.ones((3, 3), bool))
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    urban = lab == sizes.argmax()
    field_like = analysis & (hh_db_s["a"] < PARAMS["field_like_max_db"]) & \
        (hh_db_s["b"] < PARAMS["field_like_max_db"])

    # Change objects
    labels, info = bp.detect_change_objects(d_hh, analysis, PARAMS["object_core_db"],
                                            PARAMS["object_grow_db"], PARAMS["object_min_px"])
    urban_q = bp.quantiles(d_hh[urban], (1, 5, 25, 50, 75, 95, 99))
    objects = []
    idx = np.arange(1, len(info) + 1)
    cy = ndimage.mean(np.indices((H, W))[0], labels, idx)
    cx = ndimage.mean(np.indices((H, W))[1], labels, idx)
    slices = ndimage.find_objects(labels)
    ux = T.c + (np.asarray(cx) + 0.5) * T.a
    uy = T.f + (np.asarray(cy) + 0.5) * T.e
    lon, lat = warp(f"EPSG:{epsg}", "EPSG:4326", list(ux), list(uy))
    for (lbl, sign), sl, lo, la, x_, y_ in zip(info, slices, lon, lat, cx, cy):
        reg = labels[sl] == lbl
        a_raw, b_raw = hh["a"][sl][reg], hh["b"][sl][reg]
        hva, hvb = hv["a"][sl][reg], hv["b"][sl][reg]
        objects.append({
            "id": int(lbl), "sign": "brightened" if sign > 0 else "darkened",
            "pixels": int(reg.sum()), "area_ha": round(reg.sum() * 0.04, 2),
            "dHH_db": round(10 * np.log10(b_raw.mean() / a_raw.mean()), 3),
            "HH_before_db": round(10 * np.log10(a_raw.mean()), 3),
            "HH_after_db": round(10 * np.log10(b_raw.mean()), 3),
            "dHV_db_unresolved": round(10 * np.log10(hvb.mean() / hva.mean()), 3),
            "centroid_px": [round(float(x_), 1), round(float(y_), 1)],
            "centroid_lonlat": [round(lo, 5), round(la, 5)],
            "bbox_px": [sl[1].start, sl[0].start, sl[1].stop, sl[0].stop],
        })
    objects.sort(key=lambda o: -o["area_ha"])

    # Optical cross-check (NASA HLS S30 NDVI on the same grid) ---------------------------
    optical = None
    hls_dir = os.path.join(ROOT, "data/raw/hls")
    if os.path.exists(os.path.join(hls_dir, "20261023_ndvi.tif")):
        def rdh(n):
            with rasterio.open(os.path.join(hls_dir, n)) as s_:
                return s_.read(1)
        n_a, n_b = rdh("20261023_ndvi.tif"), rdh("20261102_ndvi.tif")
        clear = (rdh("20261023_clear.tif") > 0) & (rdh("20261102_clear.tif") > 0)
        d_ndvi = np.where(clear, n_b - n_a, np.nan)
        P = PARAMS
        for o in objects:
            sl_ = (slice(o["bbox_px"][1], o["bbox_px"][3]), slice(o["bbox_px"][0], o["bbox_px"][2]))
            reg = labels[sl_] == o["id"]
            cl = reg & clear[sl_]
            frac = float(cl.sum() / reg.sum())
            o["optical_clear_frac"] = round(frac, 3)
            if frac >= P["optical_min_clear_frac"]:
                dn = round(float(np.median(d_ndvi[sl_][cl])), 3)  # classify on the published value
                o["NDVI_before"] = round(float(np.median(n_a[sl_][cl])), 3)
                o["NDVI_after"] = round(float(np.median(n_b[sl_][cl])), 3)
                o["dNDVI"] = round(dn, 3)
                o["optical_class"] = ("vegetation loss" if dn <= -P["ndvi_change"] else
                                      "greening" if dn >= P["ndvi_change"] else "little vegetation change")
            else:
                o["optical_class"] = "no clear optical view"
        bg = clear & analysis & (labels == 0)

        def summ(sign):
            r = [o for o in objects if o["sign"] == sign and "dNDVI" in o]
            d = np.array([o["dNDVI"] for o in r])
            return {"objects_with_clear_view": len(r),
                    "dNDVI_median": round(float(np.median(d)), 3) if len(d) else None,
                    "dNDVI_q25_q75": [round(float(v), 3) for v in np.percentile(d, [25, 75])] if len(d) else None,
                    "frac_vegetation_loss": round(float((d <= -P["ndvi_change"]).mean()), 3) if len(d) else None,
                    "frac_little_change": round(float((np.abs(d) < P["ndvi_change"]).mean()), 3) if len(d) else None,
                    "frac_greening": round(float((d >= P["ndvi_change"]).mean()), 3) if len(d) else None}
        optical = {
            "source": "NASA HLS S30 v2.0 (Sentinel-2 surface reflectance harmonized), DOI 10.5067/HLS/HLSS30.002",
            "before": {"date": "2026-10-23 (south, tile 36SYF) / 2026-10-21 (north, tile 36SYG)", "utc": "08:30",
                       "granules": ["HLS.S30.T36SYF.2026296T082011.v2.0", "HLS.S30.T36SYG.2026294T082001.v2.0"]},
            "after": {"date": "2026-11-02", "utc": "08:30",
                      "granules": ["HLS.S30.T36SYF.2026306T082551.v2.0", "HLS.S30.T36SYG.2026306T082551.v2.0"]},
            "clear_both_frac_of_analysis": round(float((clear & analysis).sum() / analysis.sum()), 3),
            "background_fields_dNDVI_median": round(float(np.median(d_ndvi[bg])), 3),
            "background_fields_dNDVI_q25_q75": [round(float(v), 3) for v in np.percentile(d_ndvi[bg], [25, 75])],
            "brightened": summ("brightened"), "darkened": summ("darkened"),
            "method": "NDVI=(B8A-B04)/(B8A+B04); Fmask cloud/adjacent/shadow/snow excluded; average-resampled to the NISAR 20 m grid; per-object median over pixels clear on both dates",
        }

    # Sensitivity of the object census to the core threshold
    sens = []
    for core in (2.0, 2.5, 3.0, 4.0, 5.0):
        lb, inf = bp.detect_change_objects(d_hh, analysis, core, min(PARAMS["object_grow_db"], core),
                                           PARAMS["object_min_px"])
        pos = sum(1 for _, s in inf if s > 0)
        area_pos = float(np.isin(lb, [i for i, s in inf if s > 0]).sum() * 0.04) if inf else 0.0
        area_neg = float(np.isin(lb, [i for i, s in inf if s < 0]).sum() * 0.04) if inf else 0.0
        sens.append({"core_db": core, "objects_brightened": pos, "objects_darkened": len(inf) - pos,
                     "area_brightened_ha": round(area_pos, 1), "area_darkened_ha": round(area_neg, 1)})

    # Layers ---------------------------------------------------------------------------
    def write(name, arr):
        p = os.path.join(OUT, name)
        np.ascontiguousarray(arr).tofile(p)
        return {"file": name, "dtype": str(arr.dtype), "shape": list(arr.shape), "sha256": sha256(p),
                "bytes": os.path.getsize(p)}

    layers = {}
    for s in "ab":
        layers[f"hh_{s}"] = write(f"hh_{s}.i16", bp.encode_db_int16(np.where(valid, bp.to_db(hh[s]), np.nan)))
        f = PARAMS["hv_block_px"]
        layers[f"hv_{s}_40m"] = write(f"hv_{s}_40m.i16", bp.encode_db_int16(bp.to_db(bp.block_mean_linear(hv[s], valid, f))))
    flags = (valid.astype(np.uint8) | (analysis.astype(np.uint8) << 1) | (urban.astype(np.uint8) << 2))
    layers["flags"] = write("flags.u8", flags)
    layers["flags"]["bits"] = {"1": "jointly valid (both dates)", "2": "analysis area (500 m edge buffer)",
                              "4": "stable urban control"}
    if optical is not None:
        for nm, arr in (("ndvi_a_40m", n_a), ("ndvi_b_40m", n_b)):
            m40 = bp.block_mean_linear(np.where(clear, arr, 0.0), clear, 2)
            enc = np.full(m40.shape, bp.INT16_NODATA, np.int16)
            ok = np.isfinite(m40)
            enc[ok] = np.round(m40[ok] * 10000).astype(np.int16)
            layers[nm] = write(f"{nm}.i16", enc)
            layers[nm]["encoding"] = "NDVI*10000, -32768 = no clear view on both dates (40 m)"
    remap = np.zeros(len(info) + 1, np.uint16)
    for new, o in enumerate(objects, start=1):
        remap[o["id"]] = new
        o["id"] = new
    layers["objects"] = write("objects.u16", remap[labels])

    # lon/lat sample grid for client-side georeferencing (bilinear between nodes)
    st = PARAMS["lonlat_grid_step_px"]
    gx = np.arange(0, W + 1, st)
    gy = np.arange(0, H + 1, st)
    GX, GY = np.meshgrid(gx, gy)
    glon, glat = warp(f"EPSG:{epsg}", "EPSG:4326", list((T.c + GX * T.a).ravel()), list((T.f + GY * T.e).ravel()))

    # Context: OSM projected to pixel coordinates
    osm = json.load(open(os.path.join(ROOT, "data/context/osm_context_raw.json")))

    def to_px(lons, lats):
        xs, ys = warp("EPSG:4326", f"EPSG:{epsg}", lons, lats)
        return [[round((x - T.c) / T.a, 1), round((y - T.f) / T.e, 1)] for x, y in zip(xs, ys)]

    ctx = {"places": [], "rivers": [], "roads": []}
    for e in osm["elements"]:
        t = e.get("tags", {})
        if e["type"] == "node" and t.get("place") in ("city", "town", "village"):
            px = to_px([e["lon"]], [e["lat"]])[0]
            if 0 <= px[0] < W and 0 <= px[1] < H:
                ctx["places"].append({"name": t.get("name"), "kind": t["place"], "px": px,
                                      "lonlat": [e["lon"], e["lat"]]})
        elif e["type"] == "way" and "geometry" in e:
            line = to_px([g["lon"] for g in e["geometry"]], [g["lat"] for g in e["geometry"]])
            if t.get("waterway") == "river":
                ctx["rivers"].append({"name": t.get("name"), "px": line})
            elif t.get("highway"):
                ctx["roads"].append({"class": t["highway"], "px": line})

    # Graticule every 0.05 degrees, projected to pixel polylines
    ctx["graticule"] = []
    lon_min, lon_max = min(glon), max(glon)
    lat_min, lat_max = min(glat), max(glat)
    step = 0.05
    for lv in np.arange(np.ceil(lon_min / step) * step, lon_max, step):
        lats = list(np.linspace(lat_min, lat_max, 40))
        ctx["graticule"].append({"kind": "lon", "value": round(float(lv), 2), "px": to_px([float(lv)] * 40, lats)})
    for av in np.arange(np.ceil(lat_min / step) * step, lat_max, step):
        lons = list(np.linspace(lon_min, lon_max, 40))
        ctx["graticule"].append({"kind": "lat", "value": round(float(av), 2), "px": to_px(lons, [float(av)] * 40)})

    power = json.load(open(os.path.join(ROOT, "data/context/power_35.8_37.0_20261018_20261108.json")))
    prec = power["properties"]["parameter"]["PRECTOTCORR"]

    # Parity samples: display-definition smoothing (valid mask) for browser self-check
    disp = {s: bp.boxcar_linear(hh[s], valid, k) for s in "ab"}
    d_disp = bp.to_db(disp["b"]) - bp.to_db(disp["a"])
    rng = np.random.default_rng(20261114)
    cand = np.flatnonzero(valid.ravel())
    pick = rng.choice(cand, 200, replace=False)
    parity = [{"i": int(i), "dHH_s": round(float(d_disp.ravel()[i]), 4)} for i in pick]

    fl = d_hh[field_like]
    case = {
        "schema": "between-passes/case@1",
        "id": "ceyhan-2026-10-22_2026-11-03",
        "title": "Ceyhan fields, Adana, Türkiye",
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grid": {"width": W, "height": H, "epsg": epsg, "posting_m": T.a,
                 "transform": [T.a, T.b, T.c, T.d, T.e, T.f],
                 "lonlat_grid": {"step_px": st, "nx": len(gx), "ny": len(gy),
                                 "lon": [round(v, 6) for v in glon], "lat": [round(v, 6) for v in glat]}},
        "acquisitions": {s: {"granule": GRANULES[s], "date": DATES[s],
                             "start_utc": GRANULES[s].split("_")[-6] if False else None} for s in "ab"},
        "params": PARAMS,
        "layers": layers,
        "stats": {
            "valid_px": int(valid.sum()), "analysis_px": int(analysis.sum()),
            "urban_control": {"px": int(urban.sum()),
                              "dHH_db_region": round(bp.region_change_db(hh["a"], hh["b"], urban), 3),
                              "dHH_px_q1_5_25_50_75_95_99": [round(v, 3) for v in urban_q]},
            "field_like": {"px": int(field_like.sum()),
                           "dHH_db_region": round(bp.region_change_db(hh["a"], hh["b"], field_like), 3),
                           "dHH_px_q5_25_50_75_95": [round(v, 3) for v in bp.quantiles(fl)],
                           "frac_gt_3db": round(float((fl >= 3).mean()), 4),
                           "frac_lt_minus3db": round(float((fl <= -3).mean()), 4)},
            "analysis_area": {"dHH_db_region": round(bp.region_change_db(hh["a"], hh["b"], analysis), 3)},
            "objects": {"count": len(objects),
                        "brightened": sum(o["sign"] == "brightened" for o in objects),
                        "darkened": sum(o["sign"] == "darkened" for o in objects),
                        "area_ha_brightened": round(sum(o["area_ha"] for o in objects if o["sign"] == "brightened"), 1),
                        "area_ha_darkened": round(sum(o["area_ha"] for o in objects if o["sign"] == "darkened"), 1)},
            "sensitivity": sens,
        },
        "objects": objects,
        "optical": optical,
        "parity_samples": parity,
        "context": ctx,
        "weather": {"source": "NASA POWER daily point, PRECTOTCORR (mm/day), community AG",
                    "point": [35.8, 37.0],
                    "series": [{"date": d, "mm": prec[d]} for d in sorted(prec)]},
    }
    for s in "ab":
        g = GRANULES[s].split("_")
        case["acquisitions"][s]["start_utc"] = g[-6]
        case["acquisitions"][s]["end_utc"] = g[-5]
        case["acquisitions"][s]["track_dir_frame"] = "151 D 070"
    with open(os.path.join(OUT, "case.json"), "w") as f:
        json.dump(case, f, separators=(",", ":"))
    s = case["stats"]
    print(json.dumps({k: v for k, v in s.items()}, indent=1))
    print("top objects:", json.dumps(objects[:5], indent=0)[:1500])
    print("sizes:", {k: v["bytes"] for k, v in layers.items()}, "case.json", os.path.getsize(os.path.join(OUT, "case.json")))


if __name__ == "__main__":
    main()
