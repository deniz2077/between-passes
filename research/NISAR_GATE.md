# NISAR data-access & comparability gate — log

Gate started: **2026-11-14 16:51 Europe/Istanbul (13:51 UTC)**. Cap: 75 min (→ 18:06 TRT), excluding time blocked waiting for the participant's own Earthdata Login.

## Step 1 — Official challenge (PASS)
`https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/` read 14 Nov via browser. Objective: interactive application using NISAR radar data to track/visualize surface change; explicitly invites a hometown study area, multiple dates/polarizations, ancillary context, and *hypothesizing physical drivers of what you see (or don't see)*. An Adana/Çukurova agricultural backscatter-change case is in scope.

## Step 2 — CMR metadata (PASS, metadata only)
Query: `https://cmr.earthdata.nasa.gov/search/granules.umm_json?short_name=NISAR_L2_GCOV_V1&point=35.8,37.0&page_size=100` → **3 hits** (not 2):

| # | GranuleUR | Start (UTC) | Track/Dir/Frame | Note |
|---|---|---|---|---|
| A | `NISAR_L2_PR_GCOV_033_151_D_070_2005_DHDH_A_20261022T162402_20261022T162437_P05036_N_F_J_001` | 2026-10-22 16:24:02 | 151 / D / 70 | pair member |
| B | `NISAR_L2_PR_GCOV_034_151_D_070_2005_DHDH_A_20261103T162403_20261103T162437_P05036_N_F_J_001` | 2026-11-03 16:24:03 | 151 / D / 70 | pair member, same stack `151_D_070` |
| C | `NISAR_L2_PR_GCOV_034_079_D_070_2005_DHDH_A_20261029T163222_20261029T163257_P05036_N_F_J_001` | 2026-10-29 16:32:22 | **079** / D / 70 | **different track → different incidence geometry**; same day as the largest POWER rain (16.49 mm). Not directly pixel-comparable with A/B; possible context only after geometry check. |

Common metadata (granule A, verified UMM): collection `NISAR_L2_GCOV_V1` v1 (concept `C3622241360-ASF`, DOI **10.5067/NIL2GCOV-V1**, FreeAndOpenData=true), product version 1.0.20, PGE `GCOV_L_PGE R05.03.2`, CRID **P05036** (VALIDATED), processing center JPL, frequencies A (HH+HV, 20 MHz) and B (HH+HV, 5 MHz), full frame, not joint obs, ingest 2026-11-11. Local time of acquisitions ≈ 19:24 TRT (evening descending pass).

Footprint A: polygon (36.12E 38.08N)–(35.31E 35.98N)–(37.98E 35.30N)–(38.83E 37.39N). Point 35.8E 37.0N is inside but only ≈0.1° (~9 km) from the western swath edge → **edge-of-swath risk** (valid-mask misalignment at L2 edges is a documented known issue). AOI may need to shift east.

## Step 2b — Calibration / known issues (checked)
- `https://nisar-docs.asf.alaska.edu/release-notes/` → **404** (page moved).
- Availability page: VALIDATED released 2026-11-06, "fully calibrated and validated", all L-band acquisitions from 2026-10-21, CRID P05036.
- VALIDATED known-issues table (`/nisar-known-issues`): only (1) incomplete L0B products — *resolved* in P05036; (2) permanent data gap 27 Jul–10 Aug 2026. **No ~1 dB radiometric caveat is listed for VALIDATED products.** The brief's "pre-Nov-12 ~1 dB in certain modes" caveat could not be located in current docs — recorded as *unverified*, not assumed either way.
- Product-level (BETA-era) issues still worth checking in our data: valid-mask misalignment at edges, RFI blobs (worse in HV), low-backscatter streaks, 77 MHz noise floor (**not our mode**: 20+5 MHz).
- GCOV diagonal terms (HHHH, HVHV) are real-valued **gamma-0 power, radiometrically terrain corrected** (GCOV doc page) → dB conversion `10·log10` is valid for these terms only. Layers also include `numberOfLooks`, `mask`, `rtcGammaToSigmaFactor`.

## Step 3 — Access (PASS, 17:00 TRT after participant set up own ~/.netrc)
Authenticated HTTP byte-range reads (`scripts/nisar_remote.py`) let h5py read only needed chunks. Metadata inspection of A: 23 MB / 11 requests / 22 s. Window extraction: A 71 MB, B 65 MB (of 1.92 GB each). Full metadata: `research/granule_A_inspect.json`.

## Step 4 — Raster verification (PASS)
- Grid: EPSG:32637 (UTM 37N), freq A 20 m posting, 17532×17784; coordinates are pixel centres (A/B-frequency grids share edge 151920 m only under that convention).
- **A and B share an identical geogrid** (same row/col indices and coordinates for the window) → no resampling needed.
- Window: centre 35.85E 37.0N, 24×24 km = 1200×1200 px, x 207680–231680, y 4087520–4111520.
- Layers: HHHH, HVHV (float32, units "1" = linear RTC γ⁰ power; output convention gamma0, linear power, RTC-AP area-based), mask (0 invalid/partially focused, 1 = subswath 1, 255 = outside), numberOfLooks (~9 median), rtcGammaToSigmaFactor, inputDataExceptionMask (768 = HH+HV fully focused, no anomaly).
- Finite fraction 99.7%; jointly valid (mask==1, exception==768, γ⁰>0 both dates) **77.5%** (west part is outside the swath).
- Look direction **Left**, descending → swath west edge = near range; incidence 33.5°–47.2° across swath.
- `noiseCorrectionApplied = False` (thermal noise not subtracted). Reported noise-equivalent backscatter in window (east part; NaN elsewhere): HH ≈ −17.5…−18.8 dB (B 0.3–0.5 dB lower than A); HV ≈ −22.9…−23.7 dB (B 0.1–0.3 dB higher). Units stated as DN² — treat as indicative.
- rfiLikelihood (freq A): HH 6.2 / 5.1; **HV 581.5 / 305.0** (A/B) → HV RFI risk flagged.

## Step 5 — First real preview + control (PASS)
Figures: `research/figures/gate_preview_A.png`, `research/figures/gate_HH_pair.png`. Stats: `research/gate_stats_A.json`. 5×5 boxcar on linear γ⁰ before dB.
- **Stable control** = largest persistently bright (HH>0 dB both dates) urban cluster in Ceyhan, 1,342 px: **ΔHH median +0.08 dB (IQR −0.14…+0.43)**.
- Field-like pixels (HH<−5 dB both dates), 883,874 px: ΔHH median +0.37 dB, p5/p25/p75/p95 = −0.90/−0.08/+0.92/+2.49 dB; **3.3% > +3 dB vs 0.4% < −3 dB** (strongly right-skewed, parcel-shaped).
- At fixed brightness, ΔHH shows **no range ramp**; darker HH fields brighten more (~+0.8–1.0 dB for −15…−11 dB fields) uniformly across range. HH noise floor decreased on B, so additive noise cannot explain the brightening.
- **HV unresolved**: ΔHV rises west→east even at fixed HV brightness (e.g. −0.15 → +1.84 dB for −15…−13 dB pixels), while the reported HV noise floor changed only ~0.3 dB. Could be a real landscape gradient or an HV-specific artifact (RFI likelihood high). **HV change will not be interpreted** unless resolved; it is shown as a documented failure mode.

## Step 6 — Verdict: **GO** (access + comparability), 17:10 TRT (gate elapsed ≈19 min)
Two authentic, calibrated, identically gridded same-track NISAR γ⁰ rasters are accessible reproducibly; HH shows a stable control and a measurable, spatially structured, parcel-scale change signal.

## Scientific failure modes to carry forward
Speckle and spatial autocorrelation; edge-of-swath mask misalignment; unsubtracted noise (dark pixels); HV RFI / ramp; parcel changes can be tillage, harvest, irrigation, crop growth or soil wetting — **cause not determinable from backscatter alone**; POWER rain is a coarse model estimate; only 2 dates on this geometry (29 Oct is track 079).

## Context data (verified)
NASA POWER daily point 35.8E/37.0N (cell elev 80.9 m), saved `data/context/power_35.8_37.0_20261018_20261108.json`. PRECTOTCORR 22 Oct–3 Nov total **27.63 mm**; 28 Oct 6.46, 29 Oct 16.49, 30 Oct 1.40, 3 Nov 1.01 mm. 4–6 Nov rain (5.97/3.99/3.62 mm) is **after** pass B and cannot appear in the A/B pair. Gridded model estimate, not a gauge.

## Third-look test — granule C (29 Oct, track 079), 14 Nov ~18:00 TRT: NO-GO
- Grid: EPSG:32636 (UTM 36N), 20 m, 17208×17496 — different projection from A/B (32637) → would need reprojection.
- Geometry: track 079 descending, incidence 33.6–47.3° across its swath (different look angle at Ceyhan than track 151).
- `calibrationInformation/frequencyA/{HH,HV}/rfiLikelihood` = **4.03×10¹⁰ / 6.65×10¹⁰** (vs 6.2 / 581 for A). Extreme RFI flag.
- Decision: not used for analysis; stated in the app's Context tab.
