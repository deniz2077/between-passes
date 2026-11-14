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

## Step 3 — Access (BLOCKED on participant login)
- Browse PNG (`..._LATLON.png`, 1976×1953 RGB) downloads without auth — **browse only, does not pass the gate**.
- `.h5` GET → 302 → `HTTP 401 Basic: Access denied` ⇒ **Earthdata Login required**.
- Plan: participant runs `python3 scripts/setup_earthdata_netrc.py` (own credentials, hidden prompt, written only to `~/.netrc`, chmod 600). Then `scripts/nisar_remote.py` does authenticated HTTP **byte-range reads** so h5py reads only the AOI window (no 2×1.8 GB downloads). Fallback: Harmony subset via Earthdata Search in browser.
- Status at 17:2x TRT: helper launched in a terminal tab, awaiting participant.

## Steps 4–7 — pending data
Raster verification (shape, CRS, transform, nodata, units, extrema), co-registration check, ROI + stable-control stats, GO/NO-GO.

## Context data (verified)
NASA POWER daily point 35.8E/37.0N (cell elev 80.9 m), saved `data/context/power_35.8_37.0_20261018_20261108.json`. PRECTOTCORR 22 Oct–3 Nov total **27.63 mm**; 28 Oct 6.46, 29 Oct 16.49, 30 Oct 1.40, 3 Nov 1.01 mm. 4–6 Nov rain (5.97/3.99/3.62 mm) is **after** pass B and cannot appear in the A/B pair. Gridded model estimate, not a gauge.
