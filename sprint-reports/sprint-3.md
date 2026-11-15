# Sprint 3 · Scale the science

**Team** Dusk Orbit · Deniz Efe Bulut (solo: Product Owner, Developer, Scrum Master)
**Event** NASA Space Apps Challenge 2026 · Niğde Local Event (virtual) · Dancing with the SARs
**Window** 14 Nov 2026, 19:15 – 20:00 (Europe/Istanbul)

## Goal
Answer the two open questions from Sprint 2: does it hold beyond one place, and was it wet soil or ploughing? Then go public.

## Planned
1. Survey every validated NISAR scene worldwide.
2. Commit the test plan before extracting any data.
3. Measure NISAR change and NASA SMAP soil moisture at randomly drawn sites.
4. Run the test exactly as planned and place Ceyhan against it.
5. Publish the repository and the live app.

## Done
- **Survey.** 15,122 validated NISAR granules form 889 repeat pairs.
- **Plan first.** Test rules committed at 19:26 (`43f2fbb`), before any value was extracted.
- **Result.** At 74 random sites, NISAR change tracks SMAP soil-moisture change: Spearman ρ = 0.58, p = 0.0001, +1.0 dB per +0.1 m³/m³. 16 of 18 sites with a clear moisture change moved the same way.
- **Ceyhan.** SMAP shows the soil there went from 0.16 to 0.36 m³/m³ across the rain. Wet soil becomes the leading explanation.
- **Public.** Repository and app live on GitHub Pages, with a worldwide-test page that re-computes the statistics in the browser.
- **23 automated tests.**

## Not done
- YouTube and Drive uploads; Niğde presentation and documentation.

## Problems and fixes
| Problem | Fix |
|---|---|
| Some NISAR frames use 10 m pixels | Fixed before analysis; listed as a deviation |
| 125 of 200 sites had no quality SMAP reading | Dropped by the pre-written rule; the possible bias is reported |
| Ceyhan itself misses the ±1-day SMAP rule | Shown only as a labelled exploratory comparison |

## Contributions
- **Deniz Efe Bulut:** conceived the project idea, the research question and the choice of location, and set the project's direction. Made every key decision, including reviewing, approving and adopting the worldwide test and its pre-registration.
- **AI (Claude Code):** coding, data analysis and document drafting; proposed the worldwide statistical test, which Deniz evaluated and approved.

## Evidence
Commits `43f2fbb` – `0f16f34` · `research/global/` · `app/world.html`

## Next sprint
Repeat the test, lock predictions, and turn the study into a product anyone can use.
