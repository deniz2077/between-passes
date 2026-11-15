# Sprint 2 · Pipeline and first prototype

**Team** Dusk Orbit · Deniz Efe Bulut (solo: Product Owner, Developer, Scrum Master)
**Event** NASA Space Apps Challenge 2026 · Niğde Local Event (virtual) · Dancing with the SARs
**Window** 14 Nov 2026, 17:20 – 18:10 (Europe/Istanbul)

## Goal
Turn the GO result into a reproducible pipeline and a working web app on the real Ceyhan data.

## Planned
1. Change detection against the stable control, with threshold sensitivity.
2. Unit and data-integrity tests.
3. Web app: before/after viewer, change map, field inspection, user-drawn regions, exports.
4. An independent check on the harvest explanation.
5. First drafts of the NASA demo and form.

## Done
- **636 changed fields** (≥ 3 dB, ≥ 1 ha). 7× more area brightened than darkened, at every threshold from 2 to 5 dB. Town-centre control: +0.12 dB.
- **Optical cross-check (NASA HLS).** Only 9% of the brightened fields lost their plants, so harvest explains a minority.
- **Web app v1.** Swipe between passes, inspect any field, draw any region and measure it live, export the evidence. The browser re-checks every published number on load.
- **19 automated tests.**
- **Drafts:** 7-slide NASA demo, form text, captioned walkthrough.

## Not done
- Public repository and live link (visibility decision pending).

## Problems and fixes
| Problem | Fix |
|---|---|
| A test caught fields classified on unrounded values | Classify on the published value; the test now guards it |
| A second optical tile created a visible seam | Kept the consistent single-tile pair; sensitivity documented |
| The 29 Oct pass looked like a useful third date | Tested and rejected for this pair: different geometry and a high interference flag |

## Contributions
- **Deniz Efe Bulut:** the project idea, the research question, the study area and every key decision.
- **AI (Claude Code):** wrote the code, ran the data analysis and drafted the documents, and suggested methods and wording that I reviewed and chose to use.

## Evidence
Commits `ca43690` – `9d76fae` · `app/` · `tests/` · `submission/deck/`

## Next sprint
Show that the result holds beyond one place, and find the cause of the change.
