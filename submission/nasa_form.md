# NASA Space Apps 2026 — Project form draft (English)

> Final draft for Deniz to review and paste into the NASA Project tab. Test both links in a private window before submitting.

## Project Name
Between Passes

## High-Level Project Summary
Between Passes is an interactive radar evidence lab built on NASA-ISRO NISAR data. It asks what changed in the farmland of Ceyhan (Adana, Türkiye) between two NISAR passes on 22 October and 3 November 2026, and why. Calibrated HH backscatter from the identical orbit shows 636 field-scale change parcels, with 7.0× more area brightened than darkened, while the town centre, a stable control, moved only +0.12 dB. NASA HLS optical data show only 9% of brightened parcels lost vegetation, so harvest explains a minority. NASA SMAP measured Ceyhan's soil moisture rising from 0.16 to 0.36 m³/m³ after the first autumn rain, making wetting the leading explanation. To test whether this holds beyond one place, I pre-registered a global test on 200 randomly drawn NISAR repeat pairs: at the 74 sites with quality SMAP data, radar change tracks soil-moisture change (ρ = 0.58, p < 0.001), and a pre-registered replication on 200 new random sites confirmed it (n = 73, ρ = 0.55, p < 0.001). Users can swipe between passes, open any parcel's evidence, draw their own region, explore every global site, and export a case file, with every number re-verified in the browser.

## Link to Project Demo
https://deniz2077.github.io/between-passes/demo/Between_Passes_NASA_demo.pdf  (7 slides, public, no login)

## Link to Final Project
https://deniz2077.github.io/between-passes/  (public web app, no login) — code: https://github.com/deniz2077/between-passes

## Detailed Project Description
**What it does.** Between Passes turns two NISAR radar observations into a verifiable investigation of surface change on one farming landscape. A judge or student can:
- swipe between the calibrated 22 Oct and 3 Nov scenes (one fixed scale) and view the ΔHH change map;
- click any of 636 detected change parcels to see its measured change, before/after values, distribution against the stable control, an optical vegetation cross-check, and which physical explanations are consistent, possible or not indicated;
- draw any region and get statistics computed live in the browser from the real data;
- follow a 6-step guided case (the "evidence ladder");
- export a case file (JSON), a CSV of all parcels, or a printable report.

**How it works.**
1. *Data selection* — NASA CMR search for VALIDATED NISAR L2 GCOV granules; two passes share track 151, descending, frame 70, CRID P05036 → identical geometry and an identical 20 m UTM grid (no resampling).
2. *Efficient access* — authenticated HTTP byte-range reads let the HDF5 reader fetch only the needed chunks (~70 MB of 1.9 GB per granule).
3. *Quality masks* — joint validity from the subswath mask and input-exception mask on both dates, plus a 500 m buffer from the swath edge.
4. *Measurement* — 100 m speckle filter on linear γ⁰; ΔdB = 10·log₁₀(after/before); region values use the ratio of mean linear power.
5. *Control* — the persistently bright centre of Ceyhan (1,342 px) changed +0.12 dB; parcels require a ≥ 3 dB seed (beyond the control's 99th percentile), 2 dB growth, ≥ 1 ha. Sensitivity from 2 to 5 dB is published: the brightened/darkened asymmetry stays 7–11×.
6. *Physical checks* — HH shows no range-dependent bias and the product's noise floor fell on the second date; HV shows an unexplained west–east gradient and a high RFI flag, so HV is shown but not interpreted.
7. *Optical cross-check* — NASA HLS S30 (23 Oct, 2 Nov), cloud-masked, resampled onto the radar grid; per-parcel NDVI change separates vegetation loss (harvest) from soil-surface change. A second tile with a mismatched baseline date produced a visible seam and was excluded.
8. *Soil moisture* — NASA SMAP L3 Enhanced (9 km, L-band radiometer, same dawn/dusk orbit as NISAR): Ceyhan's soil moisture rose from 0.16 (20 Oct) to 0.36 m³/m³ (3 Nov) after the rain (exploratory ±2-day window; the pre-registered ±1-day rule found no approved value near 22 Oct).
9. *Global test, pre-registered* — plan committed before extraction: 200 of 763 eligible NISAR repeat pairs drawn at random (seed 2026); 10 km windows; SMAP soil-moisture change as the independent measurement; Spearman ρ with a permutation test. Result: n = 74 with quality SMAP data, ρ = 0.58, p < 0.001, +1.0 dB per +0.1 m³/m³ (95% CI 0.7–1.4); 16 of 18 sites with a clear moisture change moved in the same direction. *Replication* — a second pre-registered random draw of 200 new pairs (seed 2027): n = 73, ρ = 0.55, p < 0.001, +0.78 dB per +0.1 m³/m³ (95% CI 0.45–1.11, overlapping the original). Drying is the clearer signal (median about −1 dB). A bug in my first replication run (it re-read the original sample) was caught, fixed and documented before any result was used.
10. *Verification* — 26 automated tests (unit + data integrity); on every page load the browser recomputes the control, all 636 parcel values and 200 speckle-filter pixels from the shipped data (max difference 0.005 dB); the global page recomputes ρ and the slope from the shipped sites.

**Benefits.** It lets non-specialists see a real radar change and trust (or doubt) it for the right reasons: every number traces back to NASA source granules, controls and stated limitations. Locally, it shows where Çukurova's fields changed after the first autumn rain — a starting point for field checks. The data-access step works for any NISAR GCOV granule and point.

**What I hope to achieve.** Use the next 12-day NISAR passes to separate drying soil from lasting ploughing field by field, validate with local field observations, and extend the global test to more intervals and seasons.

**Limitations (stated in the app).** Two radar dates at Ceyhan; the global test is site-scale (10 km), one interval, and 63% of drawn sites lacked quality SMAP data; Ceyhan's SMAP comparison is exploratory; cause is not measured by backscatter; pixels are spatially correlated (control-based comparison instead of pixel confidence intervals); the control is urban; HV unresolved; thermal noise not subtracted in the product; optical covers ~60% of the area; rainfall is a coarse model estimate. A case study, not an alert system.

**Tools.** Python (h5py, numpy, scipy, rasterio, requests, pytest), GDAL; static web app in HTML/CSS/JavaScript (no framework, no backend); IBM Plex fonts; OpenStreetMap context.

## Use of Artificial Intelligence (SI)
Yes. Generative AI (Claude Code, Anthropic) was used as a development assistant for writing and refactoring the Python data-processing code, the web application, automated tests, and drafts of documentation and these texts. The challenge choice, study area (my home region), research question and project decisions were mine; the AI assistant also proposed the global NASA SMAP test, its pre-registration and the next-pass prediction, which I reviewed and approved. All results are computed from NASA data by the open-source code in the repository and verified by automated tests and an in-browser integrity check. No AI-generated images, video, audio or NASA branding are used.

## NASA Data
- NASA-ISRO NISAR L2 Geocoded Polarimetric Covariance (GCOV), VALIDATED, collection NISAR_L2_GCOV_V1, DOI 10.5067/NIL2GCOV-V1, ASF DAAC: `NISAR_L2_PR_GCOV_033_151_D_070_2005_DHDH_A_20261022T162402_20261022T162437_P05036_N_F_J_001` and `NISAR_L2_PR_GCOV_034_151_D_070_2005_DHDH_A_20261103T162403_20261103T162437_P05036_N_F_J_001`.
- NASA HLS S30 v2.0 (Harmonized Landsat Sentinel-2), DOI 10.5067/HLS/HLSS30.002, LP DAAC: `HLS.S30.T36SYF.2026296T082011.v2.0`, `HLS.S30.T36SYF.2026306T082551.v2.0`.
- NASA SMAP L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture, Enhanced (SPL3SMP_E v006), NSIDC DAAC, 19 Oct–12 Nov 2026.
- 200 further NISAR L2 GCOV VALIDATED repeat pairs worldwide (granule IDs in the repository: research/global/sample.json).
- NASA POWER daily point data (PRECTOTCORR), Ceyhan and each global site.
- NASA CMR and Earthdata Login for discovery and access; NISAR Data User Guide (ASF).

## Space Agency Partner & Other Data / References
- ISRO is a NISAR mission partner (S-band not used here).
- Sentinel-2 (ESA/Copernicus) observations, via NASA HLS harmonization.
- Copernicus DEM 30 m (used inside NISAR processing, per product metadata).
- OpenStreetMap contributors (ODbL) — places, rivers, roads.
- Natural Earth 1:110m land (public domain).
- IBM Plex Sans / Mono (SIL Open Font License).
- Python libraries: numpy, scipy, h5py, rasterio/GDAL, requests, pytest, Pillow, pypdfium2, Playwright (demo recording).
- Shiroma, Lavalle & Buckley (2022), IEEE TGRS, doi:10.1109/TGRS.2022.3147472 (RTC-AP algorithm cited in product metadata).
- Claude Code (Anthropic) — AI development assistant (see SI section).

## Pre-submit checklist
- [ ] Team member names on deck slide 1 correct
- [ ] Demo link (PDF, 7 slides) opens in a private window
- [ ] App link opens in a private window (desktop + phone)
- [ ] Repo public / accessible per organizer instructions
- [ ] No image/voice/likeness of anyone under 18 in any material
- [ ] Both checkboxes ticked truthfully; **Submit for Judging** clicked; success banner screenshot saved
