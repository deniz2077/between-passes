# Pre-registration — Independent replication of the global test

Written and committed **before** any replication value was extracted (14 Nov 2026, evening TRT). The original test (`PREREGISTRATION.md`, commit 43f2fbb) found ρ = 0.577, p = 0.0001, n = 74.

## Question
Does the original result replicate on a fresh, independent random sample?

## Sample
- Same population and eligibility as the original (889 HH repeat pairs; |lat| ≤ 60° → 763).
- **Exclude the 200 pairs already used.** From the remaining 563, draw **200** by simple random sampling with `numpy.random.default_rng(2027)`, from the list sorted by (track, direction, frame).

## Everything else is identical to the original plan
Same 10 km NISAR windows, validity rules, ΔHH_site metric, SMAP SPL3SMP_E overpass/quality rule (±1 day), drop rules, Spearman ρ with a 10,000-permutation two-sided test (seed 2026), Theil–Sen slope with 2,000-resample bootstrap CI. The code paths are the same; the only change is the sample (`BP_SET=rep`).

## Replication criterion (fixed now)
The result **replicates** if the replication sample gives ρ > 0 with permutation p < 0.05. We will also report whether the replication slope's 95 % CI overlaps the original CI (+0.69 … +1.42 dB per +0.1 m³/m³), and the pooled result (both samples), clearly labelled as pooled.

Whatever the outcome, it will be reported in `RESULTS.md` and in the app.
