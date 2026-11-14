# Pre-registration — Global test: does NISAR HH change track soil wetting?

Written and committed **before** any global NISAR or SMAP values were extracted (14 Nov 2026, ~19:45 TRT). Any deviation from this plan will be listed in the results file with its reason.

## Why
The Ceyhan case leaves two explanations for field brightening: soil wetting or ploughing. One pair at one place cannot separate them. If many NISAR pairs worldwide show HH change that tracks an **independent measurement of soil-moisture change**, wetting is a demonstrated driver of NISAR HH change at site scale, and Ceyhan can be placed on that global relationship.

## Population
- All VALIDATED NISAR L2 GCOV granules in NASA CMR (`NISAR_L2_GCOV_V1`, retrieved 14 Nov 2026: 15,122 parsed granules, 21 Oct–11 Nov 2026).
- Repeat pairs = same track, direction, frame, CRID and polarisation mode containing HH (DHDH, SHSH, QPDH) on two different dates: **889 pairs**.
- Excluded a priori: frame centre |latitude| > 60° (snow/ice/freeze).

## Sample
- Simple random sample of **200** eligible pairs, `numpy.random.default_rng(2026)`, drawn from the list sorted by (track, direction, frame). If a frame has more than two dates, the earliest and latest are used.
- The Ceyhan pair is **not** part of the sample; it is evaluated separately against the result.

## NISAR measurement per site
- 10 km × 10 km window (half-width 5 km) centred on the mean of the CMR boundary points, frequency A, native grid, no resampling.
- Joint validity as in the Ceyhan case: `mask` 1–254 on both dates, `inputDataExceptionMask == 768` where present, HH γ⁰ > 0.
- Site requires ≥ 50 % jointly valid pixels.
- **Primary NISAR metric:** ΔHH_site = 10·log₁₀(mean γ⁰_B / mean γ⁰_A) over jointly valid pixels.
- Secondary: after the 5×5 linear boxcar, fraction of valid pixels with ΔHH ≥ +3 dB minus fraction ≤ −3 dB.

## Independent soil-moisture measurement
- NASA SMAP L3 Radiometer Enhanced 9 km (`SPL3SMP_E`), latest file version per day, `soil_moisture` (AM) / `soil_moisture_pm` (PM).
- EASE-Grid 2.0 (EPSG:6933) cell containing the window centre.
- Overpass choice: the SMAP overpass (AM ≈ 06:00, PM ≈ 18:00 local solar time) nearest the NISAR local solar time on the same date; if missing or flagged, the other overpass on the same date; then the nearest overpass on ±1 day. Otherwise the site is dropped.
- Quality: `retrieval_qual_flag` bit 0 must be 0 (recommended quality); value must be in 0–0.6 m³/m³.
- ΔSM = SM_B − SM_A.

## Rain context (not part of the primary test)
- NASA POWER daily PRECTOTCORR at the window centre: total between the two dates and the 3 days before each date.

## Primary test
- Spearman rank correlation ρ between ΔHH_site and ΔSM across all retained sites.
- Two-sided permutation p-value, 10,000 permutations, seed 2026.
- **Hypothesis:** ρ > 0 with p < 0.05.
- Effect size: Theil–Sen slope (dB per 0.1 m³/m³) with bootstrap 95 % CI (2,000 resamples, seed 2026).

## What will be reported regardless of outcome
- N sampled, N retained and the reason for every drop.
- ρ, p, slope and CI; a scatter plot of every site.
- Where Ceyhan's (ΔSM, ΔHH) falls relative to the global fit.
- If ρ is not significant, the result is reported as a null result and the Ceyhan interpretation stays as it is.

## Known limitations, stated in advance
- 10 km windows mix land covers; vegetation, wind over water and freezing also change HH.
- SMAP 9 km cells and NISAR windows are not identical footprints.
- One random sample; site-level, not field-level.
