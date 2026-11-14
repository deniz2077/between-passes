"""Primary analysis exactly as pre-registered (research/global/PREREGISTRATION.md).

Inputs : research/global/sites/*.json, smap.json, power.json
Outputs: research/global/results.json, research/global/RESULTS.md (numbers only),
         app/data/global/sites.json (+ thumbnails) for the web app
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
G = os.path.join(ROOT, "research", "global")
SEED = 2026  # same permutation/bootstrap seed for the replication (as pre-registered)
SET = os.environ.get("BP_SET", "")
SFX = "_" + SET if SET else ""


def sm_value(smap, cell, date, hour, max_days=1):
    """SMAP soil moisture per the pre-registered overpass rule. Returns (value, used) or (None, why)."""
    r, c = cell
    d0 = datetime.strptime(date, "%Y%m%d")
    cands = []
    for dd in [0] + [d for k in range(1, max_days + 1) for d in (-k, k)]:
        day = (d0 + timedelta(days=dd)).strftime("%Y%m%d")
        for ov, h in (("AM", 6.0), ("PM", 18.0)):
            # time distance in hours from the NISAR acquisition (local solar)
            dist = abs((dd * 24 + h) - hour)
            cands.append((abs(dd), dist, day, ov))
    cands.sort()
    tried = []
    for _, dist, day, ov in cands:
        rec = smap["days"].get(day, {}).get(f"{r},{c},{ov}")
        if rec is None:
            tried.append(f"{day}{ov}:nofile")
            continue
        sm, qf = rec[0], rec[1]
        if sm == -9999.0 or not (0 <= sm <= 0.6):
            tried.append(f"{day}{ov}:fill")
            continue
        if qf & 1:
            tried.append(f"{day}{ov}:qflag")
            continue
        return sm, dict(day=day, overpass=ov, hours_from_nisar=round(dist, 1), cell_latlon=rec[2:4])
    return None, ";".join(tried[:3])


def rain(power, k, date_a, date_b):
    p = power.get(str(k))
    if not p:
        return None
    def tot(d0, d1):
        v = [p.get(d) for d in sorted(p) if d0 <= d <= d1]
        v = [x for x in v if x is not None and x >= 0]
        return round(float(sum(v)), 2) if v else None
    da, db = datetime.strptime(date_a, "%Y%m%d"), datetime.strptime(date_b, "%Y%m%d")
    f = lambda d: d.strftime("%Y%m%d")
    return dict(between=tot(f(da + timedelta(days=1)), date_b),
                pre3_a=tot(f(da - timedelta(days=3)), date_a),
                pre3_b=tot(f(db - timedelta(days=3)), date_b))


def perm_p(x, y, n=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    r0 = stats.spearmanr(x, y).correlation
    cnt = 0
    for _ in range(n):
        if abs(stats.spearmanr(x, rng.permutation(y)).correlation) >= abs(r0) - 1e-12:
            cnt += 1
    return float(r0), (cnt + 1) / (n + 1)


def boot_slope(x, y, n=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    s = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        if len(set(x[i])) > 2:
            s.append(stats.theilslopes(y[i], x[i])[0])
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def main():
    sample = json.load(open(os.path.join(G, f"sample{SFX}.json")))
    smap = json.load(open(os.path.join(G, f"smap{SFX}.json")))
    power = json.load(open(os.path.join(G, f"power{SFX}.json"))) if os.path.exists(os.path.join(G, f"power{SFX}.json")) else {}
    rows, drops = [], []
    for p in sample["sample"]:
        fn = os.path.join(G, "sites" + SFX, f"{p['k']:03d}.json")
        if not os.path.exists(fn):
            drops.append(dict(k=p["k"], reason="not processed"))
            continue
        s = json.load(open(fn))
        if s.get("status") != "ok":
            drops.append(dict(k=p["k"], reason=s.get("reason")))
            continue
        cell = smap["cells"][str(p["k"])]
        sa, ua = sm_value(smap, cell, s["date_a"], s["local_solar_hour"])
        sb, ub = sm_value(smap, cell, s["date_b"], s["local_solar_hour"])
        if sa is None or sb is None:
            drops.append(dict(k=p["k"], reason=f"SMAP unavailable: A[{ua if sa is None else 'ok'}] B[{ub if sb is None else 'ok'}]"))
            continue
        s.update(sm_a=round(sa, 4), sm_b=round(sb, 4), dSM=round(sb - sa, 4), smap_a=ua, smap_b=ub,
                 rain=rain(power, p["k"], s["date_a"], s["date_b"]))
        rows.append(s)
    x = np.array([r["dSM"] for r in rows])
    y = np.array([r["dHH_site_db"] for r in rows])
    rho, p = perm_p(x, y)
    slope, icpt, _, _ = stats.theilslopes(y, x)
    lo, hi = boot_slope(x, y)
    y2 = np.array([r["net_frac3"] for r in rows])
    rho2, p2 = perm_p(x, y2)
    res = dict(
        n_population_pairs=sample["n_pairs"], n_eligible=sample["n_eligible"], n_sampled=len(sample["sample"]),
        n_retained=len(rows), drops=drops,
        primary=dict(spearman_rho=round(rho, 4), perm_p=round(p, 5), n=len(rows),
                     theil_sen_db_per_0p1=round(slope * 0.1, 3), intercept_db=round(icpt, 3),
                     boot95_db_per_0p1=[round(lo * 0.1, 3), round(hi * 0.1, 3)]),
        secondary_net_frac3=dict(spearman_rho=round(rho2, 4), perm_p=round(p2, 5)),
    )
    json.dump(dict(results=res, sites=rows), open(os.path.join(G, f"results{SFX}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "drops"}, indent=1))
    from collections import Counter
    print(Counter(d["reason"].split(":")[0] for d in drops))


if __name__ == "__main__":
    main()
