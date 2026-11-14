# Method — Between Passes

## Question
Between NISAR's passes on 22 Oct and 3 Nov 2026 — an interval that included the area's first significant autumn rain — which fields around Ceyhan (Adana, Türkiye) changed in L-band HH backscatter beyond a stable urban control, and what physical explanations remain possible?

## 1. Data selection
- NASA CMR (`short_name=NISAR_L2_GCOV_V1`, point 35.8E 37.0N) returned three VALIDATED GCOV granules. Two share **track 151, descending, frame 70, CRID P05036** (22 Oct and 3 Nov 2026, 16:24 UTC) and are used. The third (29 Oct, track 079) has different viewing geometry and is not compared pixel-by-pixel.
- Quantity: diagonal covariance terms HHHH and HVHV = radiometrically terrain-corrected **γ⁰ in linear power** (RTC-AP, area-based; output convention gamma0, linear power).

## 2. Access
`scripts/nisar_remote.py` wraps authenticated HTTP byte-range requests in a seekable file object so `h5py` reads only the HDF5 chunks intersecting the window (~70 MB of 1.9 GB per granule).

## 3. Comparability
- Both granules are on the **identical 20 m UTM 37N geogrid** (same row/column indices and coordinates) → no resampling.
- Joint validity: subswath `mask` in 1…254 on both dates, `inputDataExceptionMask == 768` (HH and HV fully focused, no anomaly), γ⁰ > 0 for HH and HV on both dates.
- 500 m buffer from any invalid pixel (L2 valid-sample masks are documented as misaligned near swath edges).

## 4. Measurement
- Speckle: 5×5 (100 m) valid-weighted boxcar on **linear** γ⁰, then dB.
- Change: ΔdB = 10·log₁₀(γ⁰_after / γ⁰_before).
- Regions (objects, user polygons, control): ratio of mean linear power over member pixels (not the mean of per-pixel dB).

## 5. Control
Largest connected cluster that is persistently bright (smoothed HH > 0 dB on both dates): the built-up centre of Ceyhan, 1,342 px. ΔHH +0.12 dB (region); per-pixel 1/5/25/50/75/95/99 % = −1.31 / −0.61 / −0.14 / +0.08 / +0.43 / +1.03 / +2.09 dB.

## 6. Change objects
Hysteresis on smoothed ΔHH within the analysis area: seeds |Δ| ≥ 3 dB (power ×2), grown through same-sign pixels |Δ| ≥ 2 dB (8-connectivity), minimum 25 px (1 ha). Brightening and darkening are segmented separately. The 3 dB seed exceeds the control's 99th percentile. Sensitivity to the seed (2, 2.5, 3, 4, 5 dB) is reported in the app.

## 7. Physical checks
- **HH**: binned by brightness, ΔHH shows no trend across range; the product's noise-equivalent backscatter is ~0.3–0.5 dB *lower* on 3 Nov, so additive noise cannot produce the brightening. → used.
- **HV**: ΔHV rises west→east even at fixed brightness (e.g. −0.15 → +1.84 dB for −15…−13 dB pixels) while HV noise changed only ~0.3 dB, and the product reports a high HV RFI likelihood (581 / 305). → shown with caution, not interpreted.

## 8. Optical cross-check (NASA HLS)
- HLS S30 v2.0 surface reflectance, tile 36SYF: 23 Oct (before, 0 % cloud) and 2 Nov (after), 08:30 UTC — a consistent same-tile pair covering ~60 % of the analysis area. (Adding tile 36SYG with a 21 Oct baseline reached 86 % but created a visible NDVI seam — excluded; sensitivity: 10.4 % vegetation loss instead of 9.0 %.)
- Fmask bits cloud, adjacent cloud/shadow, cloud shadow and snow excluded; NDVI = (B8A − B04)/(B8A + B04); reflectance average-resampled (Fmask: mode) onto the exact NISAR 20 m grid.
- Per object (≥ 80 % pixels clear on both dates): median ΔNDVI; class *vegetation loss* (≤ −0.10), *greening* (≥ +0.10), else *little vegetation change*.
- Result: of 310 brightened objects with a clear view, 9.0 % lost vegetation and 85.5 % show little vegetation change; median ΔNDVI +0.015 vs +0.060 for fields outside objects.

## 9. Context
NASA POWER daily PRECTOTCORR at 35.8E 37.0N: 27.63 mm between passes, 6.46 mm on 28 Oct and 16.49 mm on 29 Oct. Timing context only.

## 10. Verification
- `tests/test_science.py` — unit tests on synthetic fixtures (dB conversion, masks, edge buffer, boxcar, region estimator, hysteresis objects, encodings).
- `tests/test_case_integrity.py` — recomputes published statistics from the shipped binary layers; SHA-256 of every layer; optical class consistency.
- Browser self-check on every load (Method & sources): control, all 636 objects, 200 parity pixels of the speckle filter and the analysis area recomputed in JavaScript; max difference ≤ 0.005 dB.
