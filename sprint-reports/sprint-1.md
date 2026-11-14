# Sprint 1 Report — Problem Definition & Feasibility

- **Team:** Dusk Orbit (solo participant: Deniz Efe Bulut — Product Owner / Developer / Scrum Master)
- **Event:** NASA Space Apps Challenge 2026, Niğde Local Event (virtual)
- **Challenge:** Dancing with the SARs
- **Sprint window:** 14 Nov 2026, 16:51 – 17:20 (Europe/Istanbul). Pre-event planning briefs (challenge choice, study area, fallback options) were prepared by Deniz before this sprint.

## Sprint goal
Understand the challenge, define a scientifically honest problem, and prove — with real NASA data — that the chosen NISAR study is feasible before building any interface.

## Planned work
1. Read the official challenge statement and the 2026 Project Submission Guide.
2. Locate NISAR observations over the study area (eastern Adana / Ceyhan, Türkiye).
3. Verify calibration status and known data issues.
4. Access real radar measurements (not browse images) for two comparable dates.
5. Check comparability, compute a first change preview with a stable control.
6. Decide GO / NO-GO and fix the research question.
7. Set up repository, tracking documents and task plan.

## Completed
- Challenge and submission rules reviewed (demo ≤30 s video or ≤7 slides; English; public links; no likeness of minors; AI-use disclosure).
- NASA CMR search found **three** VALIDATED NISAR L2 GCOV granules at 35.8°E 37.0°N: 22 Oct and 3 Nov 2026 on the same track (151, descending) and 29 Oct on a different track (079).
- NISAR known-issues pages checked; no radiometric issue is listed for the VALIDATED release (CRID P05036).
- Wrote a remote reader that downloads only the needed parts of each 1.9 GB HDF5 file (~70 MB per date) using the participant's own Earthdata Login.
- Verified both dates share an **identical 20 m UTM grid**, read calibrated γ⁰ HH and HV, masks and metadata.
- First result: in a stable urban control (Ceyhan town centre) HH changed by **+0.08 dB** (median); agricultural pixels show a right-skewed, parcel-shaped HH brightening (3.3% of pixels > +3 dB vs 0.4% < −3 dB). HV shows an east–west gradient that is not yet explained and will not be interpreted.
- NASA POWER daily rainfall retrieved as context (27.63 mm between passes; 16.49 mm on 29 Oct).
- Feasibility verdict: **GO** (17:10).
- Research question approved by Deniz: *Between NISAR's passes on 22 Oct and 3 Nov 2026 — an interval that included the first significant autumn rain — which fields around Ceyhan changed in L-band HH backscatter beyond a stable urban control, and what physical explanations remain possible?*
- Local Git repository, tracking files (`PROJECT_STATUS.md`, `DECISIONS.md`, `DATA_PROVENANCE.md`, `SUBMISSION_CHECKLIST.md`) and research logs (`research/NISAR_GATE.md`, `research/COMPETITIVE_NOTES.md`) created.
- Brief competitive review of public 2026 projects (README/file-tree level).

## Not completed / carried over
- GitHub remote repository and sharing the link with the organizer (waiting for the organizer's visibility instruction).
- Live demos of competitor projects not yet opened.

## Problems and how they were handled
| Problem | Resolution |
|---|---|
| Data download requires NASA Earthdata Login | Deniz entered his own credentials locally via a helper script (stored only in `~/.netrc`, never shared) |
| Full granules are ~1.9 GB each | HTTP byte-range reading of only the needed HDF5 chunks |
| NISAR release-notes URL in planning notes returned 404 | Used the current Available Data / Known Issues pages instead |
| HV polarization shows an unexplained gradient | Flagged as a documented limitation; HH is the primary evidence channel |
| Node.js not installed | Under review for the frontend approach |

## Contributions
- **Deniz:** chose the challenge and hometown study area, wrote the project briefs, set up Earthdata access, reviewed evidence and approved the research question.
- **AI assistance (Claude Code):** used for data-access scripting, analysis code, and documentation drafting under Deniz's direction. Disclosed per competition rules.

## Evidence
Commits `8162fcd`, `b7420c6`, `7aee315`; figures in `research/figures/`; statistics in `research/gate_stats_A.json`.

## Next sprint (Sprint 2) goals
Build the reproducible processing pipeline (change objects vs. control, statistics, provenance manifest), unit tests, and the first working interactive prototype on the real case data.
