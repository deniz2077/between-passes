"""Package the global test for the web app.

Inputs : research/global/results.json, research/global/sites/*_dhh100.npy, sites/999.json (Ceyhan)
Outputs: app/data/global/global.json  (sites, results, drops, provenance, sha256 of thumbs)
         app/data/global/thumbs.u8     (N x 100 x 100 uint8 dHH thumbnails at 100 m)
Thumbnail code: 0 = no data; v in 1..255 -> dHH = (v - 128) * 0.05 dB (clipped to +/-6.35 dB)
"""
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from bp_science import decode_db_int16  # noqa: E402
from global_analyze import sm_value  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
G = os.path.join(ROOT, "research", "global")
OUT = os.path.join(ROOT, "app", "data", "global")
STEP = 0.05


def thumb100(k):
    t = decode_db_int16(np.load(os.path.join(G, "sites", f"{k:03d}_dhh100.npy")))
    if t.shape[0] == 200:  # 10 m frames: 50 m blocks -> 100 m (mean of linear ratio)
        lin = np.power(10.0, t / 10.0)
        ok = np.isfinite(lin)
        s = np.where(ok, lin, 0).reshape(100, 2, 100, 2).sum(axis=(1, 3))
        n = ok.reshape(100, 2, 100, 2).sum(axis=(1, 3))
        with np.errstate(invalid="ignore", divide="ignore"):
            t = np.where(n >= 2, 10 * np.log10(s / np.maximum(n, 1)), np.nan)
    t = t[:100, :100]
    q = np.zeros((100, 100), np.uint8)
    ok = np.isfinite(t)
    q[ok] = np.clip(np.round(t[ok] / STEP) + 128, 1, 255).astype(np.uint8)
    return q


def main():
    os.makedirs(OUT, exist_ok=True)
    R = json.load(open(os.path.join(G, "results.json")))
    smap = json.load(open(os.path.join(G, "smap.json")))
    sites, thumbs = [], []
    keep = ["k", "key", "a", "b", "date_a", "date_b", "lon", "lat", "spacing_m", "local_solar_hour",
            "valid_frac", "dHH_site_db", "HH_a_site_db", "HH_b_site_db", "frac_up3", "frac_dn3",
            "net_frac3", "sm_a", "sm_b", "dSM", "smap_a", "smap_b", "rain"]
    for s in R["sites"]:
        d = {k: s.get(k) for k in keep}
        d["thumb"] = len(thumbs)
        thumbs.append(thumb100(s["k"]))
        sites.append(d)
    # Ceyhan, same 10 km rule, evaluated separately (not part of the sample)
    cey = json.load(open(os.path.join(G, "sites", "999.json")))
    cell = smap["cells"]["ceyhan"]
    sa, ua = sm_value(smap, cell, cey["date_a"], cey["local_solar_hour"])
    sb, ub = sm_value(smap, cell, cey["date_b"], cey["local_solar_hour"])
    c = {k: cey.get(k) for k in keep}
    c.update(k="ceyhan", sm_a=sa, sm_b=sb, dSM=None if sa is None or sb is None else round(sb - sa, 4),
             smap_a=ua, smap_b=ub, thumb=len(thumbs))
    thumbs.append(thumb100(999))
    blob = np.stack(thumbs).tobytes()
    open(os.path.join(OUT, "thumbs.u8"), "wb").write(blob)
    out = dict(
        results={k: v for k, v in R["results"].items() if k != "drops"},
        drops=R["results"]["drops"], sites=sites, ceyhan=c,
        thumbs=dict(file="thumbs.u8", n=len(thumbs), size=100, pixel_m=100, step_db=STEP,
                    sha256=hashlib.sha256(blob).hexdigest()),
        provenance=dict(
            nisar="NASA-ISRO NISAR L2 GCOV VALIDATED (NISAR_L2_GCOV_V1, CRID P05036), ASF DAAC, DOI 10.5067/NIL2GCOV-V1",
            smap="NASA SMAP L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture, Enhanced (SPL3SMP_E v006), NSIDC DAAC",
            power="NASA POWER daily PRECTOTCORR",
            preregistration="research/global/PREREGISTRATION.md (commit 43f2fbb)",
        ),
    )
    json.dump(out, open(os.path.join(OUT, "global.json"), "w"), separators=(",", ":"))
    print("sites", len(sites), "thumbs", len(thumbs), "bytes", len(blob), "ceyhan", c["dSM"], c["dHH_site_db"])


if __name__ == "__main__":
    main()
