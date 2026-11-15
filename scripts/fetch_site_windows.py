"""Re-read the NISAR windows of every retained worldwide-test site (original + replication)
and keep the jointly valid HH arrays for both dates, so the app can show real before/after
imagery and a per-pixel weather filter for each site.

Same window, same validity rules as scripts/global_scan.py (it reuses its reader).
Output (not committed, reproducible): data/raw/sites/<key>.npz with hh_a, hh_b, valid, spacing.

Usage: .venv/bin/python scripts/fetch_site_windows.py [workers]
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import global_scan as gs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "sites")


def retained():
    out = []
    for f in ("results.json", "results_rep.json"):
        for s in json.load(open(os.path.join(ROOT, "research", "global", f)))["sites"]:
            out.append(s)
    return out


def job(s):
    path = os.path.join(OUT, s["key"] + ".npz")
    if os.path.exists(path):
        return s["key"], "cached"
    try:
        A = gs._read(s["a"], s["lon"], s["lat"])
        B = gs._read(s["b"], s["lon"], s["lat"])
    except Exception as e:  # recorded, not hidden
        return s["key"], f"read error {type(e).__name__}: {e}"[:200]
    if A["hh"].shape != B["hh"].shape or not np.array_equal(A["x"], B["x"]):
        return s["key"], "grid mismatch"
    va = (A["mask"] >= 1) & (A["mask"] <= 254) & np.isfinite(A["hh"]) & (A["hh"] > 0)
    vb = (B["mask"] >= 1) & (B["mask"] <= 254) & np.isfinite(B["hh"]) & (B["hh"] > 0)
    if A["exc"] is not None:
        va &= A["exc"] == 768
    if B["exc"] is not None:
        vb &= B["exc"] == 768
    v = va & vb
    hha = np.where(v, A["hh"], 0).astype(np.float32)
    hhb = np.where(v, B["hh"], 0).astype(np.float32)
    # consistency with the published site metric
    d = 10 * np.log10(hhb[v].astype(np.float64).mean() / hha[v].astype(np.float64).mean())
    np.savez_compressed(path, hh_a=hha, hh_b=hhb, valid=v, spacing=float(abs(A["x"][1] - A["x"][0])),
                        epsg=A["epsg"], x0=float(A["x"][0]), y0=float(A["y"][0]))
    return s["key"], f"ok dHH {d:+.3f} (published {s['dHH_site_db']:+.3f})"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    w = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    S = retained()
    print("sites", len(S), flush=True)
    with Pool(w) as p:
        for k, msg in p.imap_unordered(job, S):
            print(k, msg, flush=True)
