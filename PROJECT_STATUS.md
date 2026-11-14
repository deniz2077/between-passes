# PROJECT STATUS — Between Passes (Signal Foundry)

_Last updated: 2026-11-14 18:08 Europe/Istanbul_

## Deadlines
- **NASA official "Submit for Judging": Sun 15 Nov 2026 23:59 Europe/Istanbul.** Target an early basic submission, then resubmit.
- Niğde: GitHub repo link due **today (14 Nov)**; Drive package (presentation, documentation, YouTube link) — folder link + cutoff still pending from organizer.
- Repo visibility: **pending Nisa's answer** — do not change visibility until Deniz confirms.

## Phase
Sprint 2 in progress. Done since gate: pipeline + 636 change objects; NASA HLS optical cross-check (consistent tile 36SYF, 60% coverage, 9.0% of brightened objects lose vegetation); guided 6-step story (#story-N deep links); competitor live-demo + judging-guide + 2025-winner research (research/COMPETITIVE_NOTES.md); NASA 7-slide deck draft (submission/deck/*.pdf, placeholders {{TEAM_MEMBER_NAME}}, {{APP_URL}}, {{REPO_URL}}); NASA form text draft (submission/nasa_form.md); Niğde walkthrough video (submission/video/make_video.py → between_passes_walkthrough.mp4, 98 s, captions, no narration, not in git); 29 Oct pass tested → NO-GO (RFI). 19 tests pass.

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
1. GitHub: waiting for Nisa → Deniz creates repo → push → share link (due today). Then GitHub Pages (needs public) or alternative static host.
2. Deniz: confirm name for slide 1 and git author identity.
4. Sprint 2 report at end of day 1.
5. Day 2: Niğde presentation + documentation + YouTube walkthrough (captions, no voice/face), final QA, NASA form submit.

## How to run
`python3 scripts/serve.py 8765` → http://localhost:8765 (app reads app/data/ceyhan). Tests: `.venv/bin/python -m pytest tests`.

## Environment
- Python venv `.venv` (py3.9; numpy, h5py, rasterio, scipy, requests, fsspec, matplotlib, pytest).
- **Node/npm not installed** — needed for the React/Vite frontend (ask Deniz, or build a no-build static frontend).
- `gh` not installed; no Git remote yet.
