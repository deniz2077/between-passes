# Limitations

1. **Two radar dates.** One pair cannot distinguish lasting change (tillage) from transient change (wet soil drying out).
2. **Cause is not measured.** HH backscatter responds to soil moisture, roughness, vegetation structure and water. Interpretations are labelled *consistent / possible / not indicated*, never *confirmed*.
3. **Spatial correlation.** Pixels after multilooking and filtering are not independent; we compare against a control instead of reporting independent-pixel confidence intervals.
4. **Urban control.** The control demonstrates instrument/processing stability, not how an unchanged agricultural field behaves.
5. **HV unresolved.** West–east ΔHV gradient at fixed brightness and high RFI likelihood; HV is not interpreted.
6. **Thermal noise not subtracted** in the product (`noiseCorrectionApplied = False`); very dark pixels carry a larger noise share.
7. **Swath edge.** West of the window is outside the swath; a 500 m buffer is applied.
8. **Thresholds are choices.** 3 dB seed / 2 dB grow / 1 ha; sensitivity 2–5 dB shown. The brightened ÷ darkened area ratio stays between 7× and 11×.
9. **Optical cross-check.** HLS dates differ from radar by up to ~1.5 days; only ~60 % of the analysis area has a consistent cloud-free same-tile pair (the northern tile would need a different baseline date and showed a seam, so it is excluded). NDVI cannot separate wet from ploughed bare soil.
10. **Rainfall** is a NASA POWER gridded estimate (~0.5°), not a gauge.
11. **Single case study.** Not an operational monitoring or alert system.
