# PROJECT STATUS — Between Passes (Signal Foundry)

_Last updated: 2026-11-14 ~17:30 Europe/Istanbul_

## Deadlines
- **NASA official "Submit for Judging": Sun 15 Nov 2026 23:59 Europe/Istanbul.** Target an early basic submission, then resubmit.
- Niğde: GitHub repo link due **today (14 Nov)**; Drive package (presentation, documentation, YouTube link) — folder link + cutoff still pending from organizer.
- Repo visibility: **pending Nisa's answer** — do not change visibility until Deniz confirms.

## Phase
Sprint 1 (framing + feasibility). NISAR gate **in progress — BLOCKED on Earthdata Login**.

## Verified
- Official challenge text read (fits a hometown backscatter-change study).
- Official submission guide read (≤30 s video OR ≤7 slides; no minors' likeness; SI disclosure; English; public links).
- CMR: 3 VALIDATED GCOV granules at 35.8E/37.0N (A 22 Oct & B 3 Nov on track 151; C 29 Oct on track 079). See `research/NISAR_GATE.md`.
- VALIDATED known issues: no radiometric caveat listed for P05036.
- POWER rainfall numbers in the brief reproduced exactly.
- HDF5 download requires Earthdata Login (401 without).

## Blocker
Deniz must enter his own Earthdata credentials in the terminal tab running `python3 scripts/setup_earthdata_netrc.py` (or run it himself). No credentials go through chat.

## Next actions (literal)
1. After `~/.netrc` exists: `.venv/bin/python scripts/inspect_granule.py <GranuleUR_A> research/granule_A_inspect.json`
2. Read a ~10×10 km HHHH/HVHV window from A and B around the AOI (shift east if near swath edge), verify grids match.
3. First ΔdB preview + stable control → GO/NO-GO report to Deniz.

## Environment
- Python venv `.venv` (py3.9; numpy, h5py, rasterio, scipy, requests, fsspec, matplotlib, pytest).
- **Node/npm not installed** — needed for the React/Vite frontend (ask Deniz, or build a no-build static frontend).
- `gh` not installed; no Git remote yet.
