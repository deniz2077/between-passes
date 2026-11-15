"""Prediction 2: the same fields, seen from two OTHER NISAR orbits, wet day -> dry day.

NISAR also passes over Ceyhan on track 079 (descending, evening) and track 071 (ascending, dawn).
Both flew on 29 Oct 2026, the rain day (NASA SMAP at Ceyhan: 0.29 m3/m3 on 28 Oct), and again on
10 Nov 2026, when the soil had dried (SMAP 0.13 m3/m3; NASA POWER: no rain 7-11 Nov).
The 10 Nov data were acquired but NOT yet released by NASA when this prediction was locked.

If the 508 fields that brightened between 22 Oct and 3 Nov (track 151) did so because the soil was
WET, then on each of these orbits they will DARKEN from 29 Oct to 10 Nov, more than the farmland
around them. If they brightened because they were PLOUGHED (rougher), they will not.

Each orbit is compared only with itself (same viewing angle, same grid, no resampling of radar
values). The track-151 field outlines are carried onto each orbit's grid by geographic position.

  python scripts/predict_two_orbits.py lock                 -> research/prediction/prediction2.json
  python scripts/predict_two_orbits.py score <079|071> <GranuleUR of the 10 Nov pass>
                                                            -> research/prediction/score2_<orbit>.json

The criteria below are fixed in `lock` and must not be edited after the 10 Nov data are released.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform

sys.path.insert(0, os.path.dirname(__file__))
import bp_science as bp  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw")
CASE = os.path.join(ROOT, "app", "data", "ceyhan")
OUTD = os.path.join(ROOT, "research", "prediction")

ORBITS = {
    "079": dict(
        name="track 079 descending (evening pass)",
        ref="NISAR_L2_PR_GCOV_034_079_D_070_2005_DHDH_A_20261029T163222_20261029T163257_P05036_N_F_J_001",
        expect="NISAR L2 GCOV VALIDATED, cycle 035, track 079 D, frame 070, CRID P05036 (acquired 10 Nov 2026 ~16:32 UTC)",
        folder="win_079"),
    "071": dict(
        name="track 071 ascending (dawn pass)",
        ref="NISAR_L2_PR_GCOV_034_071_A_020_2005_DHDH_A_20261029T024440_20261029T024515_P05036_N_F_J_001",
        expect="NISAR L2 GCOV VALIDATED, cycle 035, track 071 A, frame 020, CRID P05036 (acquired 10 Nov 2026 ~02:44 UTC)",
        folder="win_071"),
}

CRITERIA = {
    "passes": "for each orbit separately: 29 Oct 2026 (reference, wet) -> 10 Nov 2026 (dry), identical grid",
    "groups": "B = pixels inside the 508 brightened fields (track-151 outlines carried onto the orbit's grid by "
              "position); F = surrounding farmland: pixels in no changed field, not urban, darker than -5 dB HH on "
              "both track-151 dates; U = Ceyhan urban control. All pixels: valid on both dates (mask 1..254, "
              "exception mask 768, gamma0 > 0), inside the track-151 analysis area, 500 m from invalid pixels",
    "metric": "dB = 10*log10(sum gamma0_10Nov / sum gamma0_29Oct) over a group (pooled linear HH). "
              "Relative change = dB(B) - dB(F)",
    "Q1_pooled": "relative change <= -1.0 dB (the brightened fields darken at least 1 dB more than the farmland around them)",
    "Q2_most_fields": "at least two thirds of the brightened fields (those with >= 25 pixels on the orbit's grid) "
                      "darken more than the surrounding farmland (field dB < dB(F))",
    "Q3_control": "urban control |dB(U)| <= 0.5 dB, otherwise the orbit is not comparable -> inconclusive",
    "verdict_per_orbit": "Q1 and Q2 met -> CONFIRMED (wet soil); relative change >= 0 -> REFUTED (stayed bright: "
                         "roughness/ploughing); otherwise MIXED; Q3 failed -> INCONCLUSIVE",
    "void_if": [
        "the 10 Nov granule for that orbit is missing, not VALIDATED, or not on the identical grid",
        "rain before the 10 Nov pass: NASA POWER >= 10 mm over 7-10 Nov at 35.8E 37.0N. "
        "(Known at lock: 0.0 mm on each of 7, 8, 9, 10 and 11 Nov, and NASA SMAP 0.134 m3/m3 on 10 Nov AM, "
        "so the weather condition is already met.)",
    ],
}


def _rd(path):
    with rasterio.open(path) as s:
        return s.read(1), s.transform, s.crs


def _case_layers():
    C = json.load(open(os.path.join(CASE, "case.json")))
    W, H = C["grid"]["width"], C["grid"]["height"]
    obj = np.fromfile(os.path.join(CASE, "objects.u16"), np.uint16).reshape(H, W)
    flags = np.fromfile(os.path.join(CASE, "flags.u8"), np.uint8).reshape(H, W)
    hh_a = bp.decode_db_int16(np.fromfile(os.path.join(CASE, "hh_a.i16"), np.int16).reshape(H, W))
    hh_b = bp.decode_db_int16(np.fromfile(os.path.join(CASE, "hh_b.i16"), np.int16).reshape(H, W))
    fieldlike = np.isfinite(hh_a) & np.isfinite(hh_b) & (hh_a < -5) & (hh_b < -5)
    return C, obj, flags, fieldlike


def map_labels(shape, own_transform, own_crs, case_transform, case_crs, case_arrays):
    """Nearest case-grid value for every pixel centre of the orbit's own grid (pure, unit-tested).
    Returns one array per case array, 0/False where the own pixel falls outside the case grid."""
    H, W = shape
    cols, rows = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    xs = own_transform.c + cols * own_transform.a
    ys = own_transform.f + rows * own_transform.e
    if str(own_crs) != str(case_crs):
        xs, ys = warp_transform(own_crs, case_crs, xs.ravel(), ys.ravel())
        xs, ys = np.asarray(xs).reshape(H, W), np.asarray(ys).reshape(H, W)
    cc = np.floor((xs - case_transform.c) / case_transform.a).astype(int)
    rr = np.floor((ys - case_transform.f) / case_transform.e).astype(int)
    ch, cw = case_arrays[0].shape
    inside = (cc >= 0) & (cc < cw) & (rr >= 0) & (rr < ch)
    out = []
    for arr in case_arrays:
        o = np.zeros((H, W), arr.dtype)
        o[inside] = arr[rr[inside], cc[inside]]
        out.append(o)
    return out


def pooled_db(lin_ref, lin_new, m):
    return float(10 * np.log10(lin_new[m].sum() / lin_ref[m].sum()))


def relative_change(hh_ref, hh_new, obj_own, ids, B, F, U, min_px=25):
    """Pooled and per-field change, relative to surrounding farmland (pure, unit-tested)."""
    dF = pooled_db(hh_ref, hh_new, F)
    dB = pooled_db(hh_ref, hh_new, B)
    dU = float(10 * np.log10(hh_new[U].mean() / hh_ref[U].mean()))
    per = {}
    for i in ids:
        m = B & (obj_own == i)
        if m.sum() < min_px:
            continue
        d = pooled_db(hh_ref, hh_new, m)
        per[int(i)] = dict(n=int(m.sum()), dHH=round(d, 3), rel=round(d - dF, 3))
    frac = float(np.mean([p["rel"] < 0 for p in per.values()])) if per else float("nan")
    return dict(dB_brightened=round(dB, 3), dB_farmland=round(dF, 3), relative=round(dB - dF, 3),
                dB_control=round(dU, 3), n_fields=len(per), frac_fields_darker=round(frac, 3)), per


def verdict(r):
    if abs(r["dB_control"]) > 0.5:
        return "INCONCLUSIVE (control moved)"
    q1 = r["relative"] <= -1.0
    q2 = r["frac_fields_darker"] >= 2 / 3
    if q1 and q2:
        return "CONFIRMED: wet soil"
    if r["relative"] >= 0:
        return "REFUTED: fields stayed bright (roughness/ploughing)"
    return "MIXED"


def _own(folder, date):
    hh, T, crs = _rd(os.path.join(folder, f"{date}_A_HHHH.tif"))
    mask, _, _ = _rd(os.path.join(folder, f"{date}_A_mask.tif"))
    exc, _, _ = _rd(os.path.join(folder, f"{date}_A_inputDataExceptionMask.tif"))
    v = (mask >= 1) & (mask <= 254) & (exc == 768) & np.isfinite(hh) & (hh > 0)
    return hh.astype("float64"), v, T, crs


def _groups(orbit, v_joint):
    C, obj, flags, fieldlike = _case_layers()
    T_case = rasterio.Affine(*C["grid"]["transform"])
    folder = os.path.join(RAW, ORBITS[orbit]["folder"])
    _, _, T, crs = _own(folder, "20261029")
    obj_o, flg_o, fl_o = map_labels(v_joint.shape, T, crs, T_case, f"EPSG:{C['grid']['epsg']}",
                                    [obj, flags, fieldlike])
    ids = [o["id"] for o in C["objects"] if o["sign"] == "brightened"]
    v = bp.edge_buffer(v_joint, 25) & ((flg_o & 2) > 0)
    B = v & np.isin(obj_o, ids)
    F = v & (obj_o == 0) & fl_o & ((flg_o & 4) == 0)
    U = v & ((flg_o & 4) > 0)
    return C, ids, obj_o, B, F, U


def lock():
    os.makedirs(OUTD, exist_ok=True)
    out = dict(locked_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               criteria=CRITERIA, orbits={})
    for k, o in ORBITS.items():
        folder = os.path.join(RAW, o["folder"])
        hh, v, T, crs = _own(folder, "20261029")
        C, ids, obj_o, B, F, U = _groups(k, v)
        win = json.load(open(os.path.join(folder, "20261029_A_window.json")))
        lvl = lambda m: round(float(10 * np.log10(hh[m].mean())), 3)  # noqa: E731
        out["orbits"][k] = dict(
            name=o["name"], reference_granule=o["ref"], expected_pass=o["expect"],
            grid=dict(epsg=win["epsg"], x_first_last=win["x_first_last"], y_first_last=win["y_first_last"],
                      center_lonlat=win["center_lonlat"], half_km=win["half_km"]),
            reference_hh_sha256=hashlib.sha256(open(os.path.join(folder, "20261029_A_HHHH.tif"), "rb").read()).hexdigest(),
            n_px=dict(brightened=int(B.sum()), farmland=int(F.sum()), control=int(U.sum())),
            n_fields_mapped=int(len([i for i in ids if (B & (obj_o == i)).sum() >= 25])),
            reference_level_db=dict(brightened=lvl(B), farmland=lvl(F), control=lvl(U)),
        )
    out["case_objects_sha256"] = hashlib.sha256(open(os.path.join(CASE, "objects.u16"), "rb").read()).hexdigest()
    out["context"] = dict(
        smap_ceyhan_recommended=[["20261026", "PM", 0.0534], ["20261028", "PM", 0.2909], ["20261102", "AM", 0.2679],
                                 ["20261103", "AM", 0.356], ["20261105", "PM", 0.2315], ["20261110", "AM", 0.1337],
                                 ["20261111", "PM", 0.0976]],
        power_ceyhan_mm={"20261028": 6.46, "20261029": 16.49, "20261107": 0.0, "20261108": 0.0, "20261109": 0.0,
                         "20261110": 0.0, "20261111": 0.0},
        cmr_check="NASA CMR queried 15 Nov 2026 ~00:20 UTC: no cycle-035 granule over Ceyhan for track 079 or 071 "
                  "(newest NISAR GCOV anywhere: 12 Nov). The 10 Nov data were acquired but not yet released.",
    )
    json.dump(out, open(os.path.join(OUTD, "prediction2.json"), "w"), indent=1)
    json.dump({k: out[k] for k in ("locked_utc", "criteria", "context")}
              | {"orbits": {k: {kk: v[kk] for kk in ("name", "expected_pass", "n_fields_mapped")}
                            for k, v in out["orbits"].items()}},
              open(os.path.join(CASE, "prediction2.json"), "w"), indent=1)
    print(json.dumps(out["orbits"], indent=1))


def score(orbit, gid_new):
    pred = json.load(open(os.path.join(OUTD, "prediction2.json")))
    p = pred["orbits"][orbit]
    folder = os.path.join(RAW, ORBITS[orbit]["folder"])
    lon, lat = p["grid"]["center_lonlat"]
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "extract_window.py"), gid_new, str(lon), str(lat),
                    str(p["grid"]["half_km"]), folder], check=True)
    d_new = gid_new.split("_A_")[1][:8]
    side = json.load(open(os.path.join(folder, f"{d_new}_A_window.json")))
    if side["x_first_last"] != p["grid"]["x_first_last"] or side["y_first_last"] != p["grid"]["y_first_last"]:
        raise SystemExit("VOID: the new pass is not on the identical grid")
    sha = hashlib.sha256(open(os.path.join(folder, "20261029_A_HHHH.tif"), "rb").read()).hexdigest()
    if sha != p["reference_hh_sha256"]:
        raise SystemExit("reference data changed since the lock")
    hh0, v0, _, _ = _own(folder, "20261029")
    hh1, v1, _, _ = _own(folder, d_new)
    C, ids, obj_o, B, F, U = _groups(orbit, v0 & v1)
    r, per = relative_change(hh0, hh1, obj_o, ids, B, F, U)
    r["verdict"] = verdict(r)
    res = dict(scored_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), orbit=orbit,
               granule_new=gid_new, **r, Q1=r["relative"] <= -1.0, Q2=r["frac_fields_darker"] >= 2 / 3,
               Q3=abs(r["dB_control"]) <= 0.5,
               note="Check the void conditions before publishing.", fields=per)
    json.dump(res, open(os.path.join(OUTD, f"score2_{orbit}.json"), "w"), indent=1)
    app = os.path.join(CASE, "prediction2_result.json")
    allres = json.load(open(app)) if os.path.exists(app) else {}
    allres[orbit] = {k: v for k, v in res.items() if k != "fields"}
    json.dump(allres, open(app, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "fields"}, indent=1))


if __name__ == "__main__":
    {"lock": lambda: lock(), "score": lambda: score(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
