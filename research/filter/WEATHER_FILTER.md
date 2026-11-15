# The weather filter: rules fixed before computing

Written and committed on 15 Nov 2026 (~11:45 TRT), before any per-pixel filter result was computed for the worldwide sites. The site-level numbers it uses (NISAR ΔHH, SMAP ΔSM) already exist from the pre-registered test; the per-pixel classification below does not.

## Why
Radar change maps are how satellites watch the ground through cloud. But wet soil looks brighter to L-band radar and dry soil darker, so rain and drying make change maps light up with change that is only weather. In the worldwide test, at sites where SMAP soil moisture changed by at least 0.05 m³/m³, a median 5.1 % of the land changed by ≥ 3 dB, against 0.18 % at sites where it changed by ≤ 0.02 m³/m³ (147 sites, original + replication).

The physics gives the filter its rule: **wetting can only brighten, drying can only darken.** A change that goes against the soil-moisture change cannot be explained by it.

## Inputs (per site, already measured)
- NISAR L2 GCOV HH, two passes on the same track 12 days apart, same 10 × 10 km window and validity rules as the worldwide test.
- NASA SMAP soil-moisture change ΔSM for the same days (pre-registered rule; Ceyhan uses its labelled exploratory ±2-day value).

## Rules
1. **Weather signal.** ΔSM ≥ +0.05 → soil got *wetter*; ΔSM ≤ −0.05 → *drier*; otherwise *steady*.
2. **Changed land.** After the 5 × 5 linear boxcar (as in the test), pixels with ΔHH ≥ +3 dB (brighter) or ≤ −3 dB (darker). 3 dB is the threshold used for the Ceyhan change objects.
3. **Each changed pixel** is
   - *could be the weather* if the soil got wetter and the pixel got brighter, or the soil got drier and the pixel got darker;
   - *beyond the weather* otherwise, including every changed pixel where the soil was steady.
4. **Site verdict.**
   - Changed land < 1 % of valid pixels → **Quiet**.
   - Else, soil wetter or drier and ≥ 2/3 of the changed land *could be the weather* → **Mostly the weather**.
   - Else → **Real change beyond the weather**.
5. **Expected shift (context only).** The pre-registered fit (+1.02 dB per +0.1 m³/m³, intercept −0.13 dB) gives the site-wide change the soil moisture alone would predict; it is shown next to the measured change, not used in the verdict.

## What it is and is not
- A **screening filter**: it tells you which changes the weather cannot explain, so you know where to look. It does not say what the real change was (harvest, ploughing, flooding, building, fire, wind on water…).
- "Could be the weather" is not proof of weather. Ceyhan's brightened fields are in this group; the three locked predictions test them.
- SMAP sees 9 km cells; a local shower inside a "steady" cell would show as "beyond the weather". Vegetation growth, freezing and wind on water also change radar.
- Thresholds (0.05 m³/m³, 3 dB, 1 %, 2/3) are choices made here, before computing; they are not tuned.
