# Sprint 2 Report — Pipeline, Prototype & First Submission Drafts

- **Team:** Dusk Orbit (solo participant: Deniz Efe Bulut — Product Owner / Developer / Scrum Master)
- **Event:** NASA Space Apps Challenge 2026, Niğde Local Event (virtual)
- **Challenge:** Dancing with the SARs
- **Sprint window:** 14 Nov 2026, 17:20 – 18:10 (Europe/Istanbul)

## Sprint goal
Turn the GO result from Sprint 1 into a reproducible processing pipeline and a working, public-ready web app on the real Ceyhan data, then draft the NASA demo.

## Planned work
1. Change objects against the urban control, threshold sensitivity, frozen case dataset with hashes.
2. Unit and data-integrity tests.
3. Interactive web app: viewer, swipe, change map, objects, user regions, evidence panel, exports.
4. An independent check on the "harvest" explanation.
5. Study the competition and judging guide; draft the NASA 7-slide demo and form text.

## Completed
- **Case pipeline** (`scripts/build_case.py`): 636 change objects (3 dB seed, 2 dB growth, ≥ 1 ha); brightened 3,282 ha vs darkened 468 ha (**7.0×**); urban control +0.12 dB; asymmetry stays 7–11× for seeds of 2–5 dB. Frozen dataset in `app/data/ceyhan/` with SHA-256 per layer.
- **Tests:** 19 automated tests (unit + integrity) passing.
- **Web app v1** (static, no backend, no login): swipe between passes, ΔHH map, click any object for its evidence, draw any region with live statistics, census table, JSON/CSV/report export, and an **in-browser integrity check** that recomputes the published numbers from the shipped data on every load.
- **Optical cross-check:** NASA HLS (Sentinel-2) NDVI resampled onto the radar grid. Only **9 %** of brightened objects with a clear view lost vegetation, so harvest explains a minority.
- **Guided case:** a 6-step "evidence ladder" (measure → is it real? → is it harvest? → what remains).
- **Competitive research:** opened the strongest public competitor's live demo; read the 2026 judging guide and studied 2025 winners. Target awards: Best Use of Science, Local Impact.
- **Submission drafts:** NASA 7-slide deck (PDF), all NASA form fields, a captioned walkthrough video.

## Not completed / carried over
- Public GitHub repository (waiting for the organizer's visibility decision).
- Public app link, so the deck and form still have link placeholders.

## Problems and how they were handled
| Problem | Resolution |
|---|---|
| An integrity test found objects classified on unrounded ΔNDVI while the published value was rounded | Classify on the published value; test now guards it |
| Adding a second optical tile (21 Oct baseline) created a visible seam (14.3 % vs 9.0 % vegetation loss) | Used the consistent single-tile pair (60 % coverage); sensitivity documented |
| Rain figure in the guided case was wrong (28 mm) | Corrected to ~23 mm on 28–29 Oct |
| Deck claimed the pipeline works on "any NISAR pair" | Softened: only the data-access step is general so far |
| A third NISAR pass (29 Oct) looked useful | Tested and rejected: different projection/geometry and an extreme RFI flag |
| The browser would not hide the cover screen | A CSS rule overrode `hidden`; added a global rule |

## Contributions
- **Deniz:** kept the project on NISAR when offered the SPHEREx fallback, reviewed results and drafts, chose the slide deck over a 30-second video for NASA.
- **AI assistance (Claude Code):** wrote and tested the pipeline and app code and drafted the documents under Deniz's direction. Disclosed per competition rules.

## Evidence
Commits `ca43690` through `9d76fae` on 14 Nov (17:21 – 18:07); `app/`, `tests/`, `submission/deck/`; competitive research notes (kept private).

## Retrospective
The honest weak spots after this sprint were: one radar pair at one place, and no headline answer (wetting or ploughing). Sprint 3 takes both on.

## Next sprint (Sprint 3) goals
Scale the science beyond one site with a pre-registered global test, and give the Ceyhan case a defensible headline answer.
