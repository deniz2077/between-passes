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


## The weather filter
```bash
.venv/bin/python scripts/fetch_site_windows.py 10      # re-reads the 147 test-site windows (needs Earthdata Login)
.venv/bin/python scripts/build_sites.py                # applies the fixed rules, writes app/data/sites/
.venv/bin/python scripts/build_hero.py                 # front-page images from the Ceyhan layers
```

## Run it on any place
```bash
.venv/bin/python scripts/bp_check.py --lat 38.75 --lon -101.33 --name "Western Kansas, USA"
```
Writes `results/<name>/` with before/after images, the filtered change map, `report.json` and `report.md`. It needs two NISAR passes on the same track and frame over the point, at least half of the 10 km window valid, and quality-approved SMAP soil moisture within a day of both passes; otherwise it stops and says why. `scripts/find_check_points.py west south east north` lists frame centres with repeat passes inside a region.
