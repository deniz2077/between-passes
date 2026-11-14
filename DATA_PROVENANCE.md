# Data provenance

## NASA NISAR — L2 GCOV, VALIDATED (primary)
- Collection: `NISAR_L2_GCOV_V1` v1, CMR concept `C3622241360-ASF`, DOI 10.5067/NIL2GCOV-V1, ASF DAAC. Free and open; NASA ESDIS data use & citation guidance.
- Granules A/B/C and metadata: see `research/NISAR_GATE.md`.
- Quantity: diagonal covariance terms HHHH / HVHV = RTC gamma-0 backscatter power (linear). dB = 10·log10(γ⁰).
- Access: HTTPS via Earthdata Login; window reads by HTTP Range (`scripts/nisar_remote.py`).
- Processing: see "Processing (implemented)" below.

## NASA POWER — daily point (context only)
- `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M&community=AG&longitude=35.8&latitude=37.0&start=20261018&end=20261108&format=JSON`
- Saved: `data/context/power_35.8_37.0_20261018_20261108.json` (retrieved 14 Nov 2026).
- Gridded estimate (coarse cell), not a rain gauge; used as context, never as cause.

## Processing (implemented)
1. `scripts/extract_window.py` — 24×24 km window, centre 35.85E 37.0N, native EPSG:32637 20 m grid (rows 5888–7088, cols 2788–3988), layers HHHH, HVHV, mask, numberOfLooks, rtcGammaToSigmaFactor, inputDataExceptionMask → `data/raw/win_A/*.tif` + JSON sidecars (not committed; reproducible).
2. `scripts/build_case.py` — joint validity (mask 1..254, exception==768, γ⁰>0 both dates); 500 m edge buffer; 5×5 valid-weighted boxcar on linear γ⁰; ΔdB; urban control = largest cluster HH>0 dB both dates; hysteresis change objects (3 dB seed / 2 dB grow / 25 px); sensitivity 2–5 dB; HV at 40 m (2×2 linear block mean).
3. Output `app/data/ceyhan/`: `hh_a.i16`, `hh_b.i16` (dB×100, −32768 nodata, 20 m), `hv_*_40m.i16`, `flags.u8` (1 valid, 2 analysis, 4 control), `objects.u16`, `case.json` (stats, objects, SHA-256 of every layer, parity samples, context, weather).
4. Integrity: `tests/test_case_integrity.py` and the browser self-check recompute statistics from the shipped layers (max diff ≤ 0.005 dB).

## OpenStreetMap context
Overpass API query (places town/village/city, rivers, motorway/trunk/primary) for bbox 36.875,35.69,37.115,36.02; base timestamp 2026-11-14T14:18:06Z; saved `data/context/osm_context_raw.json`. © OpenStreetMap contributors, ODbL.

## NASA HLS S30 v2.0 — optical cross-check
- CMR `short_name=HLSS30, version=2.0`, bbox 35.72,36.90,35.98,37.10, 10 Oct–14 Nov 2026.
- Before: `HLS.S30.T36SYF.2026296T082011.v2.0` (23 Oct, 0 % cloud), `HLS.S30.T36SYG.2026294T082001.v2.0` (21 Oct, 15 %). After: `HLS.S30.T36SYF.2026306T082551.v2.0`, `HLS.S30.T36SYG.2026306T082551.v2.0` (2 Nov). 3 Nov granule rejected (covers 1 % of window). Tiles 37SBA added nothing (same swath edge).
- Bands B04, B8A, Fmask via GDAL /vsicurl with Earthdata cookies; average/mode reprojection to the NISAR grid (`scripts/extract_hls.py` → `data/raw/hls/`, not committed).
- Shipped: `ndvi_a_40m.i16`, `ndvi_b_40m.i16` (NDVI×10000, 2×2 mean of pixels clear on both dates); per-object NDVI stats in `case.json`.
- DOI 10.5067/HLS/HLSS30.002 (LP DAAC).
