# Sprint 3 Report — Scale the Science, Find the Headline, Go Public

- **Team:** Signal Foundry (solo participant: Deniz Efe Bulut — Product Owner / Developer / Scrum Master)
- **Event:** NASA Space Apps Challenge 2026, Niğde Local Event (virtual)
- **Challenge:** Dancing with the SARs
- **Sprint window:** 14 Nov 2026, 19:15 – 20:00 (Europe/Istanbul)

## Sprint goal
Answer the two weaknesses identified in the Sprint 2 retrospective: (1) one radar pair at one place — *does it scale?* and (2) no headline answer — *wetting or ploughing?* Then make the project public.

## Planned work
1. Survey every validated NISAR scene worldwide for comparable repeat pairs.
2. Write and commit a pre-registered test before extracting any data.
3. Extract NISAR windows at randomly drawn sites and an independent soil-moisture measurement (NASA SMAP) for each.
4. Run the test exactly as planned; place Ceyhan relative to the result.
5. Build a global page in the app; update the case's interpretation, the deck and the NASA form.
6. Create the public GitHub repository, deploy the app, record a ≤60 s demo video for Niğde.

## Completed
- **Survey:** NASA CMR lists 15,122 VALIDATED NISAR GCOV granules (21 Oct – 11 Nov 2026) forming **889** HH repeat pairs.
- **Pre-registration** committed at 19:26 (`research/global/PREREGISTRATION.md`, commit `43f2fbb`) before any global value was extracted.
- **Extraction:** 200 randomly drawn pairs (seed 2026), 10 × 10 km NISAR windows read by HTTP range requests; NASA SMAP L3 Enhanced soil moisture for every site and date; NASA POWER rain as context.
- **Result (as pre-registered):** at the 74 sites with quality SMAP data, NISAR HH change tracks SMAP soil-moisture change — Spearman **ρ = 0.58, p = 0.0001**, **+1.0 dB per +0.1 m³/m³** (95 % CI 0.69–1.42). 16 of 18 sites with a clear moisture change moved in the same direction. **Hypothesis supported.**
- **Ceyhan headline:** SMAP readings at Ceyhan jump from 0.05–0.16 before the rain to 0.29–0.36 m³/m³ after it (exploratory, ±2-day window). Wetting is now the evidence-backed **leading explanation**; ploughing still cannot be excluded field by field.
- **App:** new Global test page (world map, scatter, per-site radar maps, in-browser recomputation of ρ and slope); case Interpretation and guided steps 5–6 updated.
- **Public:** repository `github.com/deniz2077/between-passes` (public, per the organizer's decision), app live on GitHub Pages; push uses a deploy key limited to this one repository.
- **Submission materials:** 7-slide NASA deck with real links (also published at `/demo/` on the site); NASA form text final draft; 45.8 s real-motion captioned demo video for Niğde.
- Tests: 23 passing (4 new for the global pipeline, on synthetic inputs).

## Not completed / carried over
- YouTube upload (Deniz's account) and Niğde Drive upload (folder link pending from organizer).
- Niğde documentation PDF and presentation.
- Final QA in a private window and on a phone; NASA "Submit for Judging" (Deniz).

## Problems and how they were handled
| Problem | Resolution |
|---|---|
| Some NISAR frames use 10 m pixels; the valid-fraction check assumed 20 m | Fixed before analysis (no site changed status); documented as a deviation |
| A first patch for that bug mis-scaled every site | Caught immediately from the output, reverted exactly, re-checked |
| Stopping one run killed the SMAP download's worker processes, which then hung | Restarted SMAP with per-day caching so it can resume |
| One NISAR read hit a transient HTTP 502 | Re-read once (succeeded); documented |
| 125 of 200 sites had no quality-approved SMAP reading within ±1 day | Dropped by the pre-registered rule; reported, with the bias it may cause |
| Ceyhan itself fails the ±1-day SMAP rule | Shown only as a labelled exploratory comparison (±2 days) |
| Draft text claimed "six continents" and "all but two" sites | Replaced with verified facts (45° S–56° N; Ceyhan's wetting exceeds every sampled site) |
| Demo recording: guided card left open, wrong map mode, missed click | Fixed the script and re-recorded twice; checked stills |

## Contributions
- **Deniz:** set the goal to scale and find a headline, chose captions over narration, signed in to GitHub and authorised the public repository, reviewed results.
- **AI assistance (Claude Code):** proposed the SMAP-based global test and the pre-registration, wrote and ran the pipeline, app and documents, created the repository and Pages deployment at Deniz's request. Disclosed per competition rules.

## Evidence
Commits `43f2fbb` (pre-registration) through this report; `research/global/` (plan, per-site records, SMAP/POWER values, results); `app/world.html`; `submission/deck/Between_Passes_NASA_demo.pdf`.

## Next sprint (Sprint 4) goals
Quality assurance and submission: Niğde documentation and presentation, YouTube and Drive uploads, private-window and phone checks, NASA form submission by Deniz, Sprint 4 report before final submission.
