# Between Passes

**A radar evidence lab for Earth's changing surface** — NASA Space Apps Challenge 2026 · *Dancing with the SARs* · Team Signal Foundry (Deniz Efe Bulut, Niğde Local Event)

**Live app:** https://deniz2077.github.io/between-passes/ · **Global test:** https://deniz2077.github.io/between-passes/world.html · **Demo (7 slides):** https://deniz2077.github.io/between-passes/demo/Between_Passes_NASA_demo.pdf

Twelve days. Two NASA-ISRO **NISAR** radar passes. One farming landscape around **Ceyhan, Adana (Türkiye)** — and then **200 randomly drawn NISAR sites worldwide**.

## Headline
- **Ceyhan:** between 22 Oct and 3 Nov 2026, 7.0× more field area brightened than darkened, while a stable town control held (+0.12 dB). NASA HLS rules out harvest for most parcels, and **NASA SMAP measured the soil there go from 0.16 (20 Oct) to 0.36 m³/m³ (3 Nov)** after the first autumn rain (exploratory: ±2-day SMAP window). **Wetting is the leading explanation**; ploughing can't be excluded field by field.
- **Worldwide (pre-registered):** across 74 random NISAR sites with quality SMAP data, **radar change tracks soil-moisture change** (Spearman ρ 0.58, permutation p < 0.001; +1.0 dB per +0.1 m³/m³; 16 of 18 sites with a clear moisture change moved in the same direction). The plan was committed before any value was extracted — see [`research/global/PREREGISTRATION.md`](research/global/PREREGISTRATION.md) and [`RESULTS.md`](research/global/RESULTS.md).

## Research question
*Between NISAR's passes on 22 Oct and 3 Nov 2026 — an interval that included the area's first significant autumn rain — which fields around Ceyhan changed in L-band HH backscatter beyond a stable urban control, and what physical explanations remain possible?*

## What we measured (real NISAR VALIDATED data)
| | Value |
|---|---|
| Analysis area | 404 km² at 20 m (1,010,074 valid pixels) |
| Stable urban control (Ceyhan centre) | ΔHH **+0.12 dB** (pixel IQR −0.14 … +0.43) |
| Change objects (≥ 3 dB seed, ≥ 1 ha) | **508 brightened (3,282 ha)** vs **128 darkened (468 ha)** |
| Brightened ÷ darkened area | **7.0×** at 3 dB; between 7× and 11× for thresholds 2–5 dB |
| Optical cross-check (NASA HLS NDVI, 23 Oct → 2 Nov) | Of 310 brightened objects with a clear view, **9.0 % lost vegetation**; 85.5 % show little vegetation change (median ΔNDVI +0.015 vs +0.060 for other fields) |
| ΔHV | **Unresolved** — west–east gradient + high RFI-likelihood flag; shown, not interpreted |

Possible explanations (not determinable from backscatter alone): wetter soil after ~23 mm of rain on 28–29 Oct (27.6 mm over the whole interval) (NASA POWER estimate), tillage, harvest, standing water. The optical cross-check makes **harvest unlikely for most brightened parcels**, leaving soil-surface change (moisture and/or roughness) as the leading candidates. The app shows which are *consistent* with each selection and what evidence would decide between them.

## Features
- **Radar viewer** — both calibrated γ⁰ HH scenes on one fixed stretch, a swipe comparison, a ΔHH change map and a cautioned ΔHV map; pan/zoom, map context (OpenStreetMap), lat/lon grid, pixel readout.
- **Change objects** — 636 parcel-scale objects detected by hysteresis thresholding; click any to inspect, or deep-link (`#object-12`).
- **Draw your own region** — statistics are computed live in the browser from the real data (ratio of mean linear power), compared with the control.
- **Evidence panel** — Observed / Context / Interpretation / Limitations, with a selection-vs-control histogram.
- **Optical cross-check** — NASA HLS (Sentinel-2) NDVI resampled onto the radar grid: a ΔNDVI view and a per-object vegetation-change class.
- **The interval** — NASA POWER rainfall between passes with acquisition times.
- **Change census** — sortable object table and threshold-sensitivity chart.
- **Case file export** — JSON (geometry, statistics, sources, parameters, limitations), CSV of all objects, printable report.
- **Global test page** (`world.html`) — world map of the 200 drawn sites, radar-vs-SMAP scatter, a 10 km ΔHH map for every retained site, Ceyhan's SMAP time series, and an in-browser recomputation of ρ and the slope.
- **Integrity check on every load** — the browser recomputes the published statistics from the shipped layers and shows pass/fail (Method & sources).

## Run locally
```bash
python3 scripts/serve.py 8765        # then open http://localhost:8765
```
No login, API key or build step. All case data are frozen in `app/data/ceyhan/`.

## Reproduce the data
```bash
python3 -m venv .venv && .venv/bin/pip install numpy h5py rasterio scipy requests pytest
python3 scripts/setup_earthdata_netrc.py              # your own free NASA Earthdata Login
.venv/bin/python scripts/extract_window.py NISAR_L2_PR_GCOV_033_151_D_070_2005_DHDH_A_20261022T162402_20261022T162437_P05036_N_F_J_001 35.85 37.0 12 data/raw/win_A
.venv/bin/python scripts/extract_window.py NISAR_L2_PR_GCOV_034_151_D_070_2005_DHDH_A_20261103T162403_20261103T162437_P05036_N_F_J_001 35.85 37.0 12 data/raw/win_A
.venv/bin/python scripts/extract_hls.py
.venv/bin/python scripts/build_case.py
.venv/bin/python -m pytest tests
```
Global test (same seed → same sites and numbers):
```bash
.venv/bin/python scripts/global_scan.py sample && .venv/bin/python scripts/global_scan.py nisar 8
.venv/bin/python scripts/global_scan.py smap 4 && .venv/bin/python scripts/global_scan.py power
.venv/bin/python scripts/global_analyze.py && .venv/bin/python scripts/global_export.py
```

`extract_window.py` reads only the needed HDF5 chunks over HTTP byte ranges (~70 MB of 1.9 GB per granule).

## Repository
```
app/                 static web app (HTML/CSS/ES modules, no build) + frozen case data
scripts/             data access, window extraction, case builder, science functions
tests/               unit tests (synthetic fixtures) + case-integrity tests
research/            feasibility gate log, competitive notes, figures; research/global/ = pre-registered global test
docs/                method, data sources, limitations, AI use
sprint-reports/      Niğde Scrum sprint reports
```

## Data & credits
- NASA-ISRO NISAR L2 GCOV VALIDATED, `NISAR_L2_GCOV_V1`, DOI [10.5067/NIL2GCOV-V1](https://doi.org/10.5067/NIL2GCOV-V1), ASF DAAC.
- NASA HLS S30 v2.0, DOI [10.5067/HLS/HLSS30.002](https://doi.org/10.5067/HLS/HLSS30.002), LP DAAC.
- NASA SMAP L3 Radiometer Global Daily 9 km Soil Moisture, Enhanced (SPL3SMP_E v006), NSIDC DAAC.
- NASA POWER daily point data (PRECTOTCORR).
- Natural Earth 1:110m land (public domain), via world-atlas.
- © OpenStreetMap contributors (ODbL) — places, rivers, roads.
- Fonts: IBM Plex Sans / Mono (SIL OFL).

See [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) and [`docs/`](docs/).

## AI use
Generative AI (Claude Code) assisted with software development, data-processing code and documentation. The research question, study area and project decisions were made by the participant. All numbers are computed from NASA data by the code in this repository and are re-verified by tests and in the browser. No AI-generated imagery is used.

## License
Code: MIT (see `LICENSE`). Data remain under their providers' terms.

*Not an official NASA or ISRO product.*
