# NASA Space Apps 2026 — Project form draft (English)

> Draft for Deniz to review. Fill `{{…}}` placeholders. Do not submit until links are tested in a private window.

## Project Name
Between Passes

## High-Level Project Summary
Between Passes is an interactive radar evidence lab built on NASA-ISRO NISAR data. It compares two NISAR passes over the farmland of Ceyhan (Adana, Türkiye) on 22 October and 3 November 2026 — an interval that included the season's first significant rain — and asks which fields changed beyond a stable control, and which explanations survive the evidence. Using calibrated, terrain-corrected HH backscatter from the identical orbit, it detects 636 field-scale change parcels: 7.0× more area brightened (3,282 ha) than darkened (468 ha), while Ceyhan's town centre, our stable control, changed by only +0.12 dB. A NASA HLS optical cross-check shows that only 9% of brightened parcels lost vegetation, so harvest explains a minority; the remaining signal points to the soil surface — wetting or ploughing. Users can swipe between passes, open any parcel, draw their own region (statistics computed live from the real data), follow a one-minute guided case, and export a case file. It matters because radar sees through cloud, but a change map alone is easy to over-interpret; Between Passes shows what can and cannot be concluded.

## Link to Project Demo
{{DEMO_URL}}  (7-slide PDF: `submission/deck/Between_Passes_NASA_demo.pdf` — public link, no login)

## Link to Final Project
{{APP_URL}}  (public web app, no login) — code: {{REPO_URL}}

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
8. *Verification* — 19 automated tests (unit + data integrity); on every page load the browser recomputes the control, all 636 parcel values and 200 speckle-filter pixels from the shipped data (max difference 0.005 dB) and shows the result.

**Benefits.** It lets non-specialists see a real radar change and trust (or doubt) it for the right reasons: every number traces back to NASA source granules, controls and stated limitations. Locally, it shows where Çukurova's fields changed after the first autumn rain — a starting point for field checks. The data-access step works for any NISAR GCOV granule and point.

**What we hope to achieve.** Add further 12-day NISAR passes to separate drying soil from lasting ploughing, validate with local field observations, and generalise the case builder to any NISAR pair.

**Limitations (stated in the app).** Two radar dates only; cause is not measured by backscatter; pixels are spatially correlated (control-based comparison instead of pixel confidence intervals); the control is urban; HV unresolved; thermal noise not subtracted in the product; optical covers ~60% of the area; rainfall is a coarse model estimate. A case study, not an alert system.

**Tools.** Python (h5py, numpy, scipy, rasterio, requests, pytest), GDAL; static web app in HTML/CSS/JavaScript (no framework, no backend); IBM Plex fonts; OpenStreetMap context.

## Use of Artificial Intelligence (SI)
Yes. Generative AI (Claude Code, Anthropic) was used as a development assistant for writing and refactoring the Python data-processing code, the web application, automated tests, and drafts of documentation and these texts. The challenge choice, study area (my home region), research question and project decisions were mine. All results are computed from NASA data by the open-source code in the repository and verified by automated tests and an in-browser integrity check. No AI-generated images, video, audio or NASA branding are used.

## NASA Data
- NASA-ISRO NISAR L2 Geocoded Polarimetric Covariance (GCOV), VALIDATED, collection NISAR_L2_GCOV_V1, DOI 10.5067/NIL2GCOV-V1, ASF DAAC: `NISAR_L2_PR_GCOV_033_151_D_070_2005_DHDH_A_20261022T162402_20261022T162437_P05036_N_F_J_001` and `NISAR_L2_PR_GCOV_034_151_D_070_2005_DHDH_A_20261103T162403_20261103T162437_P05036_N_F_J_001`.
- NASA HLS S30 v2.0 (Harmonized Landsat Sentinel-2), DOI 10.5067/HLS/HLSS30.002, LP DAAC: `HLS.S30.T36SYF.2026296T082011.v2.0`, `HLS.S30.T36SYF.2026306T082551.v2.0`.
- NASA POWER daily point data (PRECTOTCORR), 35.8°E 37.0°N, 18 Oct–8 Nov 2026.
- NASA CMR and Earthdata Login for discovery and access; NISAR Data User Guide (ASF).

## Space Agency Partner & Other Data / References
- ISRO is a NISAR mission partner (S-band not used here).
- Sentinel-2 (ESA/Copernicus) observations, via NASA HLS harmonization.
- Copernicus DEM 30 m (used inside NISAR processing, per product metadata).
- OpenStreetMap contributors (ODbL) — places, rivers, roads.
- IBM Plex Sans / Mono (SIL Open Font License).
- Python libraries: numpy, scipy, h5py, rasterio/GDAL, requests, pytest, Pillow, pypdfium2.
- Shiroma, Lavalle & Buckley (2022), IEEE TGRS, doi:10.1109/TGRS.2022.3147472 (RTC-AP algorithm cited in product metadata).
- Claude Code (Anthropic) — AI development assistant (see SI section).

## Pre-submit checklist
- [ ] Team member names on deck slide 1 correct
- [ ] Demo link (PDF, 7 slides) opens in a private window
- [ ] App link opens in a private window (desktop + phone)
- [ ] Repo public / accessible per organizer instructions
- [ ] No image/voice/likeness of anyone under 18 in any material
- [ ] Both checkboxes ticked truthfully; **Submit for Judging** clicked; success banner screenshot saved
