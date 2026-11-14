# Data provenance

## NASA NISAR — L2 GCOV, VALIDATED (primary)
- Collection: `NISAR_L2_GCOV_V1` v1, CMR concept `C3622241360-ASF`, DOI 10.5067/NIL2GCOV-V1, ASF DAAC. Free and open; NASA ESDIS data use & citation guidance.
- Granules A/B/C and metadata: see `research/NISAR_GATE.md`.
- Quantity: diagonal covariance terms HHHH / HVHV = RTC gamma-0 backscatter power (linear). dB = 10·log10(γ⁰).
- Access: HTTPS via Earthdata Login; window reads by HTTP Range (`scripts/nisar_remote.py`).
- Processing: _pending_.

## NASA POWER — daily point (context only)
- `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M&community=AG&longitude=35.8&latitude=37.0&start=20261018&end=20261108&format=JSON`
- Saved: `data/context/power_35.8_37.0_20261018_20261108.json` (retrieved 14 Nov 2026).
- Gridded estimate (coarse cell), not a rain gauge; used as context, never as cause.
