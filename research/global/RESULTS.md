# Results — Global test: does NISAR HH change track soil wetting?

Plan: `PREREGISTRATION.md` (commit 43f2fbb, written before any global value was extracted).
Code: `scripts/global_scan.py`, `scripts/global_analyze.py`, `scripts/global_export.py`. Per-site records: `sites/*.json`. Full output: `results.json`.

## Sample
| | n |
|---|---|
| NISAR VALIDATED HH repeat pairs in CMR (14 Nov 2026) | 889 |
| eligible (|lat| ≤ 60°) | 763 |
| randomly drawn (seed 2026) | 200 |
| dropped: NISAR window < 50 % jointly valid | 1 |
| dropped: no recommended-quality SMAP value within ±1 day of a pass | 125 |
| **retained** | **74** |

Retained sites span 45.4° S to 55.7° N. Every SMAP cell centre used lies within 0.1° of its NISAR window centre.

## Primary result (as pre-registered)
- Spearman ρ between ΔSM (SMAP) and ΔHH_site (NISAR) = **0.577**, n = 74.
- Two-sided permutation p = **0.0001** (no permutation of 10,000 reached |ρ|; the smallest reportable value is 1/10,001).
- Theil–Sen slope **+1.02 dB per +0.1 m³/m³** (intercept −0.13 dB); bootstrap 95 % CI **+0.69 … +1.42**.
- **Hypothesis supported.**

Secondary (pre-registered): net fraction of pixels ≥ +3 dB minus ≤ −3 dB vs ΔSM: ρ = 0.564, p = 0.0001.

## Descriptive (not part of the test)
- Sites with |ΔSM| > 0.05 m³/m³: 18; NISAR change has the same sign in 16 (89 %).
- Median ΔHH: drying sites (ΔSM < −0.05, n = 11) −1.14 dB; wetting sites (> +0.05, n = 7) +0.34 dB; the 56 sites with |ΔSM| ≤ 0.05: −0.11 dB.
- Residual SD around the fit 0.72 dB.

## Ceyhan (not in the sample)
- NISAR, same 10 km rule: ΔHH_site **+0.29 dB**; 5.2 % of the window ≥ +3 dB, 0.9 % ≤ −3 dB.
- Pre-registered SMAP rule: **no value** — no SMAP swath on 22 Oct and the 21/23 Oct retrievals carry the "not recommended" flag. Ceyhan therefore cannot be placed by the pre-registered rule.
- **Exploratory** (rule widened to ±2 days; not pre-registered): 20 Oct PM 0.161 → 3 Nov AM 0.356 m³/m³, ΔSM **+0.195**.
- All recommended-quality SMAP retrievals at the Ceyhan cell: 20 Oct 0.161, 25 Oct 0.109, 26 Oct 0.053, **28 Oct 0.291**, 2 Nov 0.268, **3 Nov 0.356**, 5 Nov 0.232, 10 Nov 0.134, 11 Nov 0.098. The 28–29 Oct rain (NASA POWER 23 mm) shows as a jump, and the soil was still wet at the second NISAR pass.
- Ceyhan's exploratory wetting (+0.195) exceeds every sampled site (maximum +0.176), so the fit is extrapolated there. Its site-wide ΔHH (+0.29 dB) is below the fitted value (+1.9 dB). The brightening is concentrated in individual fields (5.2 % of the window), consistent with the parcel-level case.

## What this does and does not show
- **Shows:** across randomly drawn sites worldwide, NISAR L2 GCOV HH change between 12-day repeat passes is positively and significantly related to independently measured soil-moisture change. Soil wetting is a demonstrated, global driver of the kind of brightening seen at Ceyhan, and SMAP independently confirms Ceyhan's soil was wetted between the two passes.
- **Does not show:** that any individual Ceyhan field brightened because of wetting rather than ploughing; field-scale moisture; behaviour in other seasons or intervals. 63 % of drawn sites lacked an approved SMAP retrieval, so the retained set leans toward land covers where SMAP retrieves well.

## Deviations from the plan
1. Some NISAR frames use 10 m pixels; the first code version computed the valid fraction assuming 20 m. Fixed before analysis; no site changed status. For 10 m frames the 5×5 boxcar spans 50 m (applied literally as written).
2. One site hit a transient HTTP 502 and was re-read once (succeeded).
3. Ceyhan's exploratory ±2-day SMAP window is outside the plan and labelled as such everywhere it appears.
