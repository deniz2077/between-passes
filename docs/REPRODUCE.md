# Reproduce everything

All numbers in Between Passes come from public NASA data and the code in this repository. Same code and same random seeds give the same numbers.

## Run the app locally
```bash
python3 scripts/serve.py 8765        # then open http://localhost:8765
```
No login, API key or build step. All case data are frozen in `app/data/ceyhan/`.

## Rebuild the data
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

