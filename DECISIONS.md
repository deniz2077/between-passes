# Decisions log

| When (TRT) | Decision | Evidence / reason |
|---|---|---|
| 14 Nov 16:51 | Start with Between Passes NISAR gate; no frontend until GO | Governing briefs |
| 14 Nov ~16:5x–17:0x | Never commit organizer correspondence or the planning briefs (`.gitignore`) | Private file instructions; briefs contain personal details |
| 14 Nov ~16:5x–17:0x | Read remote HDF5 windows via authenticated byte-range requests instead of downloading 2×1.8 GB | Faster, respectful of bandwidth; Harmony is fallback |
| 14 Nov ~16:5x–17:0x | Credentials only via participant-run `scripts/setup_earthdata_netrc.py` → `~/.netrc` | Never handle passwords in chat/repo |
| 14 Nov ~16:5x–17:0x | Treat 29 Oct granule (track 079) as *not* pixel-comparable with the track-151 pair until geometry is checked | Different track ⇒ different incidence angle |
| 14 Nov ~16:5x–17:0x | "Case file + uncertainty" alone is not a differentiator; focus on calibrated γ⁰ HH/HV computation, controls, in-browser ROI stats | Earth Whisper already uses that framing (`research/COMPETITIVE_NOTES.md`) |
| 14 Nov 17:10 | NISAR gate GO; HH is the primary evidence channel; HV shown only as documented unresolved artifact/gradient | research/NISAR_GATE.md steps 4–6 |
