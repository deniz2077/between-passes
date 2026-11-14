# Competitive notes (time-boxed, 14 Nov 2026)

Inspected via GitHub API file trees + READMEs only. Live demos **not yet opened**; no code copied.

| Project | Challenge | What is demonstrably there | Observations |
|---|---|---|---|
| Earth Whisper (Dipro-UniCoder666) — live at earth-whisper.vercel.app | Dancing with the SARs | QGIS workspace with real NISAR GUNW coherence/unwrapped-phase GeoTIFFs (India), coherence-loss clusters, SRTM slope, MODIS land cover; React/Vite + FastAPI; "Event Case File", uncertainty, limitations sections; Sentinel-1 cross-check; rainfall context | Repo created 23 Sep 2026. **Framing overlaps our brief heavily** (evidence view, case file, uncertainty, "change ≠ cause"). Two hand-curated sites; README describes multiple legacy flows/demo routes. |
| LunaHorizon / "NISAR // Earth in Motion" (Aayushashsahu) | Dancing with the SARs | Real GUNW (Venezuela, P05023 PROVISIONAL), georeferencing round-trip validation records, CI, responsive checks, YouTube demo; cinematic 3D orbit intro | Explicitly marks interpretation `not_validated`. Strong reproducibility hygiene; heavy decorative intro. InSAR phase/coherence, not backscatter. |
| squeeze_test (ESuperCode) | Planet X & SPHEREx | Next.js app, Playwright e2e suite, candidate pages with multi-epoch webp stamps | Benchmark for test rigor. |
| GhostShift (ahmedatta3322) | Planet X & SPHEREx | Python two-epoch diff pipeline, blink GIFs, candidate JSON, MPC check | Small, reproducible pipeline. |

## Implications for Between Passes
1. "Evidence + case file + uncertainty" is **table stakes**, not a differentiator — Earth Whisper already does it.
2. Both NISAR rivals use **InSAR (GUNW)**. A calibrated **polarimetric backscatter (GCOV γ⁰ HH/HV)** study is a different, under-served angle.
3. Our differentiators must be *computational*: user-drawn ROI computed in-browser on real calibrated γ⁰ arrays, identically processed stable-control comparison, HH vs HV behaviour, explicit noise/stability baseline, and a reproducible export.
4. Avoid cinematic intros; get to real data in one click.

## Second pass (14 Nov ~17:45) — live demos, judging guide, 2025 winners

### Earth Whisper live (earth-whisper.vercel.app), opened and used
- Landing: cinematic Earth/satellite imagery, "Analysis with DHARA", 4-person team, lists NISAR, Sentinel-1, GPM IMERG, HLS, NASADEM.
- Investigate → Sandhya River: precomputed result for one candidate region of **5,600 m²**; NISAR coherence change −0.3263; Sentinel-1 median −2.05 dB; rainfall 3/7/14-day; **optical verification "NOT TESTED"**; "Investigation 3/4" placeholders.
- Their 4-pair "temporal fingerprint" shows only two value pairs, repeated/reversed (0.5406↔0.2143, 0.2872↔0.1753) — appears to be a data-integrity slip (observation only; not verified in their code).
- Strength: breadth of sources and multi-pair framing. Weakness: tiny showcased region, no control, no user-driven computation, optical not done.

### Official Judging & Awards Guide (2026)
- Criteria 1–5: Impact, Creativity, Validity, Relevance (NASA data as core), Presentation (demo + full project).
- Target awards for us: **Best Use of Science** ("best and most valid use of the scientific method") and **Local Impact** (hometown). Secondary: Best Use of Data.

### 2025 Global Winners studied
- Best Use of Science — SpaceGenes+ (solo, Berlin): one clear analytical idea (synergy of combined stressors) on one NASA dataset, interactive dashboard, honest "future" section, AI use disclosed.
- Local Impact — QUEÑARIS (Arequipa): strong local stakes (water security), named beneficiaries, NASA LP DAAC indices.
- Lesson: lead with stakes + audience + one memorable analytical idea; show the tool doing it.

### Strategy decisions
1. Make the **evidence ladder** the hero: measure (NISAR) → is it real? (stable control) → is it harvest? (HLS optical) → what remains (soil surface: moisture/tillage) → timing context (POWER).
2. Add a **guided story mode** (≈5 steps) so a judge sees the ladder in < 60 s, each step driving the real map.
3. Counter breadth with depth + verifiability (integrity checks, all 636 objects, user regions). Consider the 29 Oct NISAR pass (track 079) as a third look if time allows.
