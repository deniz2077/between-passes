# PROJECT STATUS — Between Passes (Signal Foundry)

_Last updated: 2026-11-14 17:35 Europe/Istanbul_

## Deadlines
- **NASA official "Submit for Judging": Sun 15 Nov 2026 23:59 Europe/Istanbul.** Target an early basic submission, then resubmit.
- Niğde: GitHub repo link due **today (14 Nov)**; Drive package (presentation, documentation, YouTube link) — folder link + cutoff still pending from organizer.
- Repo visibility: **pending Nisa's answer** — do not change visibility until Deniz confirms.

## Phase
Sprint 2 (research + prototype). Gate GO 17:10; research question approved; Sprint 1 report committed. Pipeline, tests (18 pass) and web app v1 working locally.

## Verified
- Official challenge text read (fits a hometown backscatter-change study).
- Official submission guide read (≤30 s video OR ≤7 slides; no minors' likeness; SI disclosure; English; public links).
- CMR: 3 VALIDATED GCOV granules at 35.8E/37.0N (A 22 Oct & B 3 Nov on track 151; C 29 Oct on track 079). See `research/NISAR_GATE.md`.
- VALIDATED known issues: no radiometric caveat listed for P05036.
- POWER rainfall numbers in the brief reproduced exactly.
- HDF5 download requires Earthdata Login (401 without).

## Blockers / needs from Deniz
- GitHub repo (no `gh` CLI here): Deniz creates the repo on github.com (visibility per Nisa) and shares the URL; link due to organizer **today**.
- Git author name/email (commits currently use placeholder "Signal Foundry").

## Next actions
1. Push to GitHub once repo exists; enable GitHub Pages (app/ folder) for the public judge URL.
2. Optional validity boost: NASA HLS optical NDVI before/after for top objects (harvest vs wetting/tillage).
3. docs/ (METHOD, LIMITATIONS, AI_USE), Sprint 2 report at sprint end.
4. Day 2: polish, NASA demo (≤30 s video or ≤7 slides), Niğde presentation/docs/YouTube, NASA form.

## How to run
`python3 scripts/serve.py 8765` → http://localhost:8765 (app reads app/data/ceyhan). Tests: `.venv/bin/python -m pytest tests`.

## Environment
- Python venv `.venv` (py3.9; numpy, h5py, rasterio, scipy, requests, fsspec, matplotlib, pytest).
- **Node/npm not installed** — needed for the React/Vite frontend (ask Deniz, or build a no-build static frontend).
- `gh` not installed; no Git remote yet.
