"""A falsifiable prediction for NISAR's next Ceyhan pass (track 151 D, frame 70, cycle 035, 15 Nov 2026).

If the 22 Oct -> 3 Nov brightening was mainly soil WETTING, the fields should dim back as the soil
dries (NASA SMAP at Ceyhan: 0.36 m3/m3 on 3 Nov -> 0.10 on 11 Nov). If it was mainly ROUGHNESS
(ploughing), they should stay bright.

  python scripts/predict_next_pass.py lock            -> research/prediction/prediction.json (commit before the pass)
  python scripts/predict_next_pass.py score <GranuleUR_of_15_Nov_pass>
                                                      -> research/prediction/score.json + app/data/ceyhan/prediction_result.json

The criteria below are fixed in `lock` and must not be edited after the pass.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio

sys.path.insert(0, os.path.dirname(__file__))
import bp_science as bp  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw")
CASE = os.path.join(ROOT, "app", "data", "ceyhan")
OUTD = os.path.join(ROOT, "research", "prediction")

CRITERIA = {
    "pass": "NISAR L2 GCOV VALIDATED, track 151 descending, frame 70, CRID P05036, cycle 035 (expected 15 Nov 2026 ~16:24 UTC)",
    "metric": "per brightened object: dHH_BC = 10*log10(mean gamma0_C / mean gamma0_B) over object pixels valid on A, B and C; "
              "recovery R = -dHH_BC / dHH_AB (1 = fully back to 22 Oct, 0 = stayed bright)",
    "P1_aggregate": "over all brightened-object pixels pooled: 10*log10(sum C / sum B) <= -0.5 * aggregate dHH_AB",
    "P2_median": "median recovery R across brightened objects >= 0.5",
    "P3_control": "urban control |dHH_BC| <= 0.5 dB (otherwise the pass is not comparable -> inconclusive)",
    "verdict": "P1 and P2 met -> WETTING dominant (confirmed); median R < 0.25 -> PERSISTENT (roughness/ploughing dominant); otherwise MIXED",
    "per_object_labels": "R >= 0.5 'dried back (wetting)'; R < 0.25 'stayed bright (roughness/ploughing or other)'; else 'partial'",
    "void_if": [
        "the cycle-035 granule is missing, not VALIDATED, or not on the identical grid",
        "it rained again: NASA SMAP at Ceyhan (any recommended-quality retrieval 14-16 Nov) >= 0.25 m3/m3, "
        "or, if SMAP has none, NASA POWER >= 10 mm over 12-15 Nov",
    ],
}


def _rd(path):
    with rasterio.open(path) as s:
        return s.read(1), s.transform


def _case():
    C = json.load(open(os.path.join(CASE, "case.json")))
    W, H = C["grid"]["width"], C["grid"]["height"]
    obj = np.fromfile(os.path.join(CASE, "objects.u16"), np.uint16).reshape(H, W)
    flags = np.fromfile(os.path.join(CASE, "flags.u8"), np.uint8).reshape(H, W)
    return C, obj, flags


def _layers(d, folder):
    hh, T = _rd(os.path.join(folder, f"{d}_A_HHHH.tif"))
    mask, _ = _rd(os.path.join(folder, f"{d}_A_mask.tif"))
    exc, _ = _rd(os.path.join(folder, f"{d}_A_inputDataExceptionMask.tif"))
    v = (mask >= 1) & (mask <= 254) & (exc == 768) & np.isfinite(hh) & (hh > 0)
    return hh.astype("float64"), v, T


def recovery(hh_a, hh_b, hh_c, obj, valid, ids):
    """Per-object dHH_AB, dHH_BC and recovery R (pure function, unit-tested)."""
    out = {}
    for i in ids:
        m = (obj == i) & valid
        if m.sum() < 5:
            continue
        a, b, c = hh_a[m].mean(), hh_b[m].mean(), hh_c[m].mean()
        dab, dbc = 10 * np.log10(b / a), 10 * np.log10(c / b)
        out[int(i)] = dict(n=int(m.sum()), dHH_AB=round(float(dab), 3), dHH_BC=round(float(dbc), 3),
                           R=round(float(-dbc / dab), 3) if dab != 0 else None)
    return out


def lock():
    os.makedirs(OUTD, exist_ok=True)
    C, obj, flags = _case()
    ids = [o["id"] for o in C["objects"] if o["sign"] == "brightened"]
    hh_a, va, _ = _layers("20261022", os.path.join(RAW, "win_A"))
    hh_b, vb, _ = _layers("20261103", os.path.join(RAW, "win_A"))
    v = va & vb & ((flags & 2) > 0)
    m = np.isin(obj, ids) & v
    agg_ab = 10 * np.log10(hh_b[m].sum() / hh_a[m].sum())
    soil = [o["id"] for o in C["objects"] if o["sign"] == "brightened" and o.get("optical_class") == "little vegetation change"]
    pred = dict(
        locked_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        criteria=CRITERIA,
        brightened_object_ids=ids,
        soil_subgroup_ids=soil,
        aggregate_dHH_AB_db=round(float(agg_ab), 3),
        P1_threshold_dHH_BC_db=round(float(-0.5 * agg_ab), 3),
        context=dict(
            smap_ceyhan_recommended=[["20261103", "AM", 0.356], ["20261105", "PM", 0.2315],
                                     ["20261110", "AM", 0.1337], ["20261111", "PM", 0.0976]],
            power_ceyhan_mm={"20261104": 5.97, "20261105": 3.99, "20261106": 3.62, "20261107": 0.0,
                             "20261108": 0.0, "20261109": 0.0, "20261110": 0.0, "20261111": 0.0},
        ),
        case_objects_sha256=hashlib.sha256(open(os.path.join(CASE, "objects.u16"), "rb").read()).hexdigest(),
    )
    json.dump(pred, open(os.path.join(OUTD, "prediction.json"), "w"), indent=1)
    json.dump({k: pred[k] for k in ("locked_utc", "criteria", "aggregate_dHH_AB_db", "P1_threshold_dHH_BC_db", "context")}
              | {"n_brightened": len(ids), "n_soil_subgroup": len(soil)},
              open(os.path.join(CASE, "prediction.json"), "w"), indent=1)
    print("locked", len(ids), "brightened objects; aggregate dHH_AB", round(float(agg_ab), 3), "dB")


def score(gid_c):
    pred = json.load(open(os.path.join(OUTD, "prediction.json")))
    C, obj, flags = _case()
    win = json.load(open(os.path.join(RAW, "win_A", "20261022_A_window.json")))
    lon, lat = win["center_lonlat"]
    folder = os.path.join(RAW, "win_C")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "extract_window.py"), gid_c, str(lon), str(lat),
                    str(win["half_km"]), folder], check=True)
    d_c = gid_c.split("_A_")[1][:8]
    side_c = json.load(open(os.path.join(folder, f"{d_c}_A_window.json")))
    if side_c["x_first_last"] != win["x_first_last"] or side_c["y_first_last"] != win["y_first_last"]:
        raise SystemExit("VOID: the new pass is not on the identical grid")
    hh_a, va, _ = _layers("20261022", os.path.join(RAW, "win_A"))
    hh_b, vb, _ = _layers("20261103", os.path.join(RAW, "win_A"))
    hh_c, vc, _ = _layers(d_c, folder)
    v = va & vb & vc & ((flags & 2) > 0)
    per = recovery(hh_a, hh_b, hh_c, obj, v, pred["brightened_object_ids"])
    m = np.isin(obj, pred["brightened_object_ids"]) & v
    agg_bc = 10 * np.log10(hh_c[m].sum() / hh_b[m].sum())
    urban = ((flags & 4) > 0) & v
    ctrl = 10 * np.log10(hh_c[urban].mean() / hh_b[urban].mean())
    Rs = np.array([p["R"] for p in per.values() if p["R"] is not None])
    medR = float(np.median(Rs))
    P1 = agg_bc <= pred["P1_threshold_dHH_BC_db"]
    P2 = medR >= 0.5
    P3 = abs(ctrl) <= 0.5
    verdict = ("INCONCLUSIVE (control moved)" if not P3 else
               "WETTING dominant — confirmed" if (P1 and P2) else
               "PERSISTENT — roughness/ploughing dominant" if medR < 0.25 else "MIXED")
    for p in per.values():
        r = p["R"]
        p["label"] = None if r is None else ("dried back (wetting)" if r >= 0.5 else
                                             "stayed bright (roughness/ploughing or other)" if r < 0.25 else "partial")
    res = dict(scored_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), granule_c=gid_c,
               aggregate_dHH_BC_db=round(float(agg_bc), 3), control_dHH_BC_db=round(float(ctrl), 3),
               median_R=round(medR, 3), P1=bool(P1), P2=bool(P2), P3=bool(P3), verdict=verdict,
               note="Check the void conditions (SMAP / POWER rain 12-15 Nov) before publishing.", objects=per)
    json.dump(res, open(os.path.join(OUTD, "score.json"), "w"), indent=1)
    json.dump({k: v for k, v in res.items() if k != "objects"} | {"objects": {k: [v["R"], v["label"]] for k, v in per.items()}},
              open(os.path.join(CASE, "prediction_result.json"), "w"))
    app_pred = json.load(open(os.path.join(CASE, "prediction.json")))
    app_pred["scored"] = True
    json.dump(app_pred, open(os.path.join(CASE, "prediction.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "objects"}, indent=1))


if __name__ == "__main__":
    {"lock": lambda: lock(), "score": lambda: score(sys.argv[2])}[sys.argv[1]]()
