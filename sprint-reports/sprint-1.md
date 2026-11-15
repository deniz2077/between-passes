# Sprint 1 · Problem and feasibility

**Team** Dusk Orbit · Deniz Efe Bulut (solo: Product Owner, Developer, Scrum Master)
**Event** NASA Space Apps Challenge 2026 · Niğde Local Event (virtual) · Dancing with the SARs
**Window** 14 Nov 2026, 16:51 – 17:20 (Europe/Istanbul)

## Goal
Define an honest research problem and prove, with real NASA radar data, that it can be answered before building anything.

## Planned
1. Read the challenge and the 2026 submission rules.
2. Find NISAR passes over the study area: Ceyhan, Adana (Türkiye).
3. Check calibration status and known data issues.
4. Read real calibrated radar values for two comparable dates.
5. Run a first change measurement against a stable control.
6. Decide GO / NO-GO and fix the research question.

## Done
- **Data found.** NASA's catalogue holds three VALIDATED NISAR GCOV passes over Ceyhan: 22 Oct and 3 Nov on the same orbit (track 151), and 29 Oct on another.
- **Efficient access.** A reader that downloads only the needed part of each 1.9 GB file (≈70 MB).
- **Comparability.** Both dates sit on an identical 20 m grid, so no resampling is needed.
- **First result.** The town centre, which should not change, moved +0.08 dB. Farmland shows a parcel-shaped brightening: 3.3% of pixels brighter by > 3 dB, against 0.4% darker.
- **Verdict.** GO at 17:10.
- **Research question.** Between NISAR's passes on 22 Oct and 3 Nov 2026, which fields around Ceyhan changed beyond a stable control, and what can explain it?

## Not done
- GitHub remote: waiting for the organizer's decision on repository visibility.

## Problems and fixes
| Problem | Fix |
|---|---|
| Data needs a NASA Earthdata Login | Deniz set up his own login locally; credentials never shared |
| 1.9 GB per file | Byte-range reads of only the needed window |
| HV channel shows an unexplained east–west gradient | HV kept as a documented limitation; HH is the evidence channel |

## Contributions
- **Deniz Efe Bulut:** conceived the project idea, the research question and the choice of location, and set the project's direction. Made every key decision.
- **AI (Claude Code):** coding, data analysis and document drafting.

## Evidence
Commits `8162fcd`, `b7420c6`, `7aee315` · `research/NISAR_GATE.md` · `research/gate_stats_A.json`

## Next sprint
Reproducible pipeline, tests, and a first working app on the real data.
