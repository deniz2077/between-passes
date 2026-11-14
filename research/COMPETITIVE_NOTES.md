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
