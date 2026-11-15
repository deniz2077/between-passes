# Sprint 4 · From study to product, then submit

**Team** Dusk Orbit · Deniz Efe Bulut (solo: Product Owner, Developer, Scrum Master)
**Event** NASA Space Apps Challenge 2026 · Niğde Local Event (virtual) · Dancing with the SARs
**Window** 14 Nov 2026, 20:00 – 15 Nov 2026, 16:11 (Europe/Istanbul)

## Goal
Test the claim in ways that can fail, turn the study into a product anyone can use and understand in a minute, and complete both submissions.

## Planned
1. Repeat the worldwide test on new random sites.
2. Lock predictions for upcoming NISAR passes before the data exist.
3. Turn the study into a product: a weather filter for radar change maps.
4. One clear story across the app, README, decks, video and documentation.
5. NASA project page and Submit for Judging; Niğde presentation, documentation and video.

## Done
- **Replication.** Plan committed before extraction (`7e1ffcf`). 73 new random sites: ρ = 0.55, p < 0.001. Same answer.
- **Three predictions** locked before NASA released the data: track 151 (`e3915c1`, 14 Nov 20:05) and tracks 079 and 071 (`a068d8f`, 15 Nov 03:20). The app scores them automatically as data arrive.
- **The product: "Rain fools radar. Between Passes shows what really changed."** Satellites find floods, harvests and cut-down forests by comparing two pictures of the same place, but after rain whole regions look "changed" when nothing happened. Between Passes sorts out those false alarms: wetter soil can only brighten radar and drier soil only darken it, so a change that goes against the measured soil moisture is real. For disaster teams, agencies watching farms and forests, and farmers.
  - The problem, measured: at 147 random NISAR sites, 28× more land looked "changed" where SMAP saw the soil get wetter or drier (5.0% vs 0.18%).
  - Filter rules committed before computing (`2365a8e`), then applied to all 148 places: 41 real change, 27 mostly weather, 80 quiet.
  - `bp_check.py` runs the filter on any place NISAR has flown. Run on nine farming regions: six worked (Kansas, Castilla, Free State, Punjab, Akmola, Beauce). Three stopped with a stated reason.
  - Ceyhan: 88% of the changed land could be the rain. The 128 fields that darkened are listed as "where to look first", in English and Turkish.
- **New front page and design.** Live filter demo on real data, world explorer with swipe cards and share links, prediction board. One dark design across all pages. The lab opens straight into the guided tour.
- **Plain language.** The intro, colour key, cards and lab were rewritten in everyday words for non-specialist readers, with expert numbers kept in small print.
- **Submission materials.** README, 7-slide NASA demo, 10-slide Niğde presentation, documentation PDF and a captioned demo video under one minute (name and problem, how it works, live demo, expected impact), all opening with the same pitch.
- **Checks.** 37 automated tests. Every page tested at desktop and phone widths with no console errors.
- **Restore point** before the redesign: tag `restore-2026-11-15-before-redesign`.

## Not done
- Scoring the predictions: waits for NASA to release the 10 Nov and 15 Nov passes.
- The uploads themselves: YouTube video, NASA Submit for Judging and the Niğde Drive folder. All files are ready; Deniz completes these after this report, before 23:59.

## Problems and fixes
| Problem | Fix |
|---|---|
| The project read as a study, not a product | Reframed around one problem (weather in radar change maps) with a measured size and a working filter |
| A first-time reader could not tell what the project does | Three-sentence pitch at the top of every material, an always-visible colour key, jargon moved to small print |
| Both 29 Oct passes carry a high interference flag | Checked the window (no stripes, clean mask, best alignment at zero shift), disclosed it, kept the town-centre safeguard |
| NASA servers returned HTTP 502 during checks | Retries in the command; failures reported, never hidden |
| Some demo points sat at a swath edge or had no SMAP reading | The command tries the next pair, or stops and says why; failed regions are shown on the site |
| A desert site flagged "beyond the weather" after 17 mm of rain | Rules kept as committed; its card now notes that local wetting SMAP missed is possible |

## Contributions
- **Deniz Efe Bulut:** the project idea, the research question, the study area and every key decision.
- **AI (Claude Code):** wrote the code, ran the data analysis and drafted the documents, and suggested methods and wording that I reviewed and chose to use.

## Evidence
Commits `7e1ffcf`, `e3915c1`, `a068d8f`, `2365a8e`, `a84cfba`, `fdbc4fb`, `5cc743c` · `research/filter/` · `research/prediction/` · `scripts/bp_check.py` · live app

## After the event
Publish each prediction's score in the app when NASA releases the data, whatever the result.
