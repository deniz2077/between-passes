# Prediction 2: the same fields, seen from two other orbits

**Locked and published on 15 Nov 2026 (03:20 TRT, commit a068d8f), before NASA released the data it predicts.**
The git commit on GitHub is the timestamp. Machine-readable lock: `prediction2.json`. Scorer: `scripts/predict_two_orbits.py`.

## In plain words
Between 22 October and 3 November, 508 fields near Ceyhan lit up on radar. My explanation is that the soil got wet in the first big autumn rain. The other possible explanation is ploughing, which also makes a field look brighter.

NISAR does not only fly over Ceyhan on the orbit I studied. It also passes on two other orbits, one at dusk and one at dawn. Both flew over on **29 October, the rainy day**, and again on **10 November, when the soil had dried** (NASA's SMAP satellite: 0.29 m³/m³ on 28 Oct, 0.13 on 10 Nov; no rain 7–11 Nov in NASA POWER).

**My prediction:** on both of these orbits, the 508 fields will **get darker** from 29 Oct to 10 Nov, by more than the farmland around them. Wet soil dries out; ploughed soil stays rough. If they stay bright, my explanation is wrong.

Each orbit is a separate, independent check. It sees the ground from a different angle and at a different time of day, and it never took part in choosing the fields.

The satellite had already flown on 10 November, but NASA had not released those data when I locked this. I checked NASA's catalogue just before locking: no 10 November pass over Ceyhan was listed for either orbit.

## Criteria (fixed)
For each orbit separately, comparing 29 Oct with 10 Nov on that orbit's own grid:
- **Q1:** the brightened fields, pooled together, darken by **at least 1.0 dB more** than the surrounding farmland.
- **Q2:** at least **two thirds** of the brightened fields darken more than the surrounding farmland.
- **Q3 (sanity):** Ceyhan's town centre changes by no more than 0.5 dB; otherwise the orbit is not comparable, and the result is inconclusive.
- **Verdict:** Q1 and Q2 met → **confirmed (wet soil)**. The fields stay as bright as their surroundings or get brighter → **refuted (ploughing)**. Anything else → **mixed**.

Exact definitions are in `prediction2.json` (`criteria`).

## How the fields are matched
The field outlines come from the original track-151 analysis. They are carried onto each orbit's own grid by geographic position, using the nearest pixel. Radar values are never resampled. Before locking, I checked the alignment: the 29 Oct images of both orbits match the 3 Nov track-151 image best at zero shift (to within 20 m). 494 of the 508 fields fall inside the track 079 window; all 508 fall inside track 071.

## When the test is void
- The 10 Nov granule for an orbit is missing, not VALIDATED, or not on the identical grid.
- Rain before the pass (NASA POWER ≥ 10 mm over 7–10 Nov). Already known at lock: 0 mm on each day, so this condition is met.

## Honest notes
- **Interference flag.** NASA's metadata gives both 29 Oct passes a high radio-interference likelihood for the whole frame: about 56,000 for track 071 and about 40 billion for track 079, against about 6 for the track-151 pair. Over the Ceyhan window, the images show no visible interference stripes, and the data-quality mask is clean (every pixel code 768). If interference affected 29 Oct, the town-centre check (Q3) is meant to catch it.
- **Not a repeat of the same measurement.** These orbits see the town and fields from other angles. That is why each orbit is only compared with itself, and the fields with the farmland around them.
- **Already visible on 29 Oct.** Compared with their surroundings, the fields that brightened were already partly brighter on 29 Oct. This is not part of the test, but it fits rain on 28–29 Oct.
