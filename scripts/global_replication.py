"""Replication summary as pre-registered in research/global/REPLICATION_PREREGISTRATION.md.

Inputs : research/global/results.json (original), results_rep.json (replication; run
         BP_SET=rep scripts/global_analyze.py first)
Outputs: research/global/replication.json, app/data/global/replication.json
"""
import json
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
from global_analyze import boot_slope, perm_p  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
G = os.path.join(ROOT, "research", "global")


def main():
    o = json.load(open(os.path.join(G, "results.json")))
    r = json.load(open(os.path.join(G, "results_rep.json")))
    po, pr = o["results"]["primary"], r["results"]["primary"]
    replicates = pr["spearman_rho"] > 0 and pr["perm_p"] < 0.05
    overlap = not (pr["boot95_db_per_0p1"][1] < po["boot95_db_per_0p1"][0] or
                   pr["boot95_db_per_0p1"][0] > po["boot95_db_per_0p1"][1])
    xs = np.array([s["dSM"] for s in o["sites"]] + [s["dSM"] for s in r["sites"]])
    ys = np.array([s["dHH_site_db"] for s in o["sites"]] + [s["dHH_site_db"] for s in r["sites"]])
    rho, p = perm_p(xs, ys)
    slope, icpt, _, _ = stats.theilslopes(ys, xs)
    lo, hi = boot_slope(xs, ys)
    clear = np.abs(xs) > 0.05
    out = dict(
        original=dict(n=po["n"], rho=po["spearman_rho"], p=po["perm_p"], slope=po["theil_sen_db_per_0p1"], ci=po["boot95_db_per_0p1"]),
        replication=dict(n=pr["n"], n_sampled=r["results"]["n_sampled"], rho=pr["spearman_rho"], p=pr["perm_p"],
                         slope=pr["theil_sen_db_per_0p1"], ci=pr["boot95_db_per_0p1"],
                         drops={k: v for k, v in __import__("collections").Counter(
                             d["reason"].split(":")[0] for d in r["results"]["drops"]).items()}),
        replicates=bool(replicates), slope_ci_overlap=bool(overlap),
        pooled_label="POOLED (both samples; descriptive, not a separate pre-registered test)",
        pooled=dict(n=int(len(xs)), rho=round(float(rho), 4), p=round(float(p), 5),
                    slope=round(float(slope * 0.1), 3), ci=[round(lo * 0.1, 3), round(hi * 0.1, 3)],
                    same_direction=[int((np.sign(xs[clear]) == np.sign(ys[clear])).sum()), int(clear.sum())]),
        rep_sites=[dict(k=s["k"], lon=s["lon"], lat=s["lat"], dSM=s["dSM"], dHH_site_db=s["dHH_site_db"]) for s in r["sites"]],
    )
    json.dump(out, open(os.path.join(G, "replication.json"), "w"), indent=1)
    json.dump(out, open(os.path.join(ROOT, "app", "data", "global", "replication.json"), "w"), separators=(",", ":"))
    print(json.dumps({k: v for k, v in out.items() if k != "rep_sites"}, indent=1))


if __name__ == "__main__":
    main()
