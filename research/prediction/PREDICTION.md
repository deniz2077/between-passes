# A falsifiable prediction for NISAR's next pass over Ceyhan

**Locked and published before the satellite flies over** (14 Nov 2026, evening TRT; git commit and push timestamp on GitHub).
Next pass: NISAR track 151 descending, frame 70, cycle 035, expected **15 Nov 2026 ~16:24 UTC**. Machine-readable lock: `prediction.json`. Scorer: `scripts/predict_next_pass.py score <granule>`.

## Why this is a real test
Between 22 Oct and 3 Nov, 508 Ceyhan parcels brightened (pooled **+4.14 dB**). Two explanations remain:
- **Wet soil** (rain on 28–29 Oct). NASA SMAP says Ceyhan's soil has since dried: 0.36 m³/m³ on 3 Nov → 0.23 (5 Nov) → 0.13 (10 Nov) → **0.10** (11 Nov). If wetting caused the brightening, **these parcels will dim back**.
- **Rougher soil** (ploughing). Roughness does not dry out. If ploughing caused it, **they will stay bright**.

The next pass separates them. We commit to the criteria now.

## Criteria (fixed)
- **P1 — aggregate:** pooled over all 508 brightened parcels, ΔHH(3 Nov → 15 Nov) ≤ **−2.07 dB** (at least half the brightening reverses).
- **P2 — typical parcel:** median recovery R ≥ **0.5**, where R = −ΔHH(B→C) / ΔHH(A→B) (1 = back to 22 Oct, 0 = stayed bright).
- **P3 — sanity:** Ceyhan's urban control moves by ≤ 0.5 dB; otherwise the pass is not comparable.
- **Verdict:** P1 and P2 met → **wetting dominant, confirmed**. Median R < 0.25 → **persistent: roughness/ploughing dominant**. Otherwise **mixed**. Every parcel also gets a label: dried back (R ≥ 0.5) / partial / stayed bright (R < 0.25).

## When the test is void
- The cycle-035 granule is missing, not VALIDATED, or not on the identical grid.
- It rained again: SMAP at Ceyhan (approved retrieval 14–16 Nov) ≥ 0.25 m³/m³, or, without SMAP, NASA POWER ≥ 10 mm over 12–15 Nov.

## Honest notes
- NISAR VALIDATED data have appeared about 3–6 days after acquisition, so the result is expected **after** the NASA submission deadline. The prediction is locked now; the score will be published in the app when the data exist.
- Rain fell on 4–6 Nov (13.6 mm, NASA POWER), after our second pass; SMAP shows the soil dried again by 10–11 Nov.
