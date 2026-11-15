# Decisions log

| When (TRT) | Decision | Evidence / reason |
|---|---|---|
| 14 Nov 16:51 | Start with Between Passes NISAR gate; no frontend until GO | Governing briefs |
| 14 Nov ~16:5x–17:0x | Never commit organizer correspondence or the planning briefs (`.gitignore`) | Private file instructions; briefs contain personal details |
| 14 Nov ~16:5x–17:0x | Read remote HDF5 windows via authenticated byte-range requests instead of downloading 2×1.8 GB | Faster, respectful of bandwidth; Harmony is fallback |
| 14 Nov ~16:5x–17:0x | Credentials only via participant-run `scripts/setup_earthdata_netrc.py` → `~/.netrc` | Never handle passwords in chat/repo |
| 14 Nov ~16:5x–17:0x | Treat 29 Oct granule (track 079) as *not* pixel-comparable with the track-151 pair until geometry is checked | Different track ⇒ different incidence angle |
| 14 Nov ~16:5x–17:0x | "Case file + uncertainty" alone is not a differentiator; focus on calibrated γ⁰ HH/HV computation, controls, in-browser ROI stats | That framing is common in existing SAR projects |
| 14 Nov 17:10 | NISAR gate GO; HH is the primary evidence channel; HV shown only as documented unresolved artifact/gradient | research/NISAR_GATE.md steps 4–6 |
| 14 Nov 17:25 | Static no-build web app (HTML/CSS/ES modules) instead of React/Vite | Node not installed; fewer moving parts; deploys to any static host |
| 14 Nov 17:30 | Region statistic = ratio of mean linear γ⁰; per-pixel stats only as distributions | Standard multilook estimator; avoids dB-averaging bias |
| 14 Nov 17:30 | Change objects: 3 dB seed (> control p99 +2.09), 2 dB grow, 1 ha; sensitivity 2–5 dB published | Control-anchored, transparent thresholds |
| 14 Nov 17:40 | Add NASA HLS NDVI cross-check (23/21 Oct → 2 Nov) | Separates vegetation loss (harvest) from soil-surface change; second NASA dataset |
| 14 Nov 17:45 | Classify optical change on the published (rounded) ΔNDVI | Integrity test found a boundary mismatch |
| 14 Nov ~17:55 | Optical published on consistent tile 36SYF only (23 Oct → 2 Nov), 60 % coverage | Adding 36SYG (21 Oct baseline) gave 86 % but a visible NDVI seam (north 14.3 % vs south 9.0 % vegetation loss); conclusion unchanged either way |
| 14 Nov ~17:50 | Target awards: Best Use of Science, Local Impact; guided 6-step "evidence ladder" story | Judging guide + 2025 winners study |
| 14 Nov ~18:00 | 29 Oct granule (track 079) not used as third look (superseded 15 Nov 03:20 for a same-orbit test, see below) | Different projection/geometry and RFI likelihood ~4e10 (HH) vs ~6 for the pair |
| 14 Nov ~19:15 | NASA demo = the 7-slide deck; captioned video kept only for Niğde (YouTube required there). Slide 1 member: Deniz Efe Bulut (written name only) | NASA allows ≤30 s video OR ≤7 slides; the evidence ladder needs text |
| 14 Nov ~19:25 | Scale to a pre-registered global test: 200 random NISAR repeat pairs vs NASA SMAP soil-moisture change | Answers 'does it scale' and 'wetting or ploughing' with an independent L-band measurement; plan fixed before seeing data |
| 14 Nov ~20:00 | Global test result: hypothesis supported (ρ 0.58, p 1e-4, n 74). Ceyhan placed only as labelled exploratory (±2-day SMAP window) | Pre-registered rule found no approved SMAP value near 22 Oct at Ceyhan |
| 14 Nov ~19:50 | Public repo github.com/deniz2077/between-passes created by Claude at Deniz's request; push via a repo-only deploy key; Pages via Actions | Nisa: repos public; Deniz authorised GitHub actions |
| 15 Nov 03:20 | Second prediction locked on tracks 079 D and 071 A (29 Oct → 10 Nov), before NASA released the 10 Nov data | Each orbit compared only with itself (same geometry, no radar resampling), so the 14 Nov "not a third look" concern does not apply; alignment checked (best at zero shift); interference flag disclosed; the town-centre check guards against it |
