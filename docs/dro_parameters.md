# Hurricane resilience parameters (post-hoc stress test)

Implemented in `dro_calc()` in `src/caribbean_dc_re.py`.

| Cat | p_c (share) | g_c (grid outage) | h_c (h) |
|---|---|---|---|
| 1 | 0.35 | 0.15 | 24 |
| 2 | 0.25 | 0.30 | 48 |
| 3 | 0.20 | 0.50 | 72 |
| 4 | 0.15 | 0.70 | 120 |
| 5 | 0.05 | 0.90 | 240 |

| Island | s_i | BTM (MWh) | DC IT (MW) |
|---|---|---|---|
| Trinidad | 0.3 | 30 | 5 |
| Jamaica | 0.8 | 84 | 15 |

**Basis.**
- **p_c** is chosen to be broadly consistent with the peak-intensity distribution of Atlantic hurricanes in HURDAT2 (Landsea & Franklin, 2013).
- **g_c and h_c** are engineering judgement and are not fitted.
- **s_i** is a relative exposure judgement: Trinidad sits at about 10.5°N, at the southern margin of the track.
- **ε ∈ [0, 0.2]** is a sensitivity sweep, directionally consistent with IPCC AR6 WG1 Ch. 11 projections of a higher proportion of Category 4–5 storms.

**Method caveat.** The adversarial reweighting `λ̃_c = clip(s_i p_c + ε(2g_c − 0.5))` is a surrogate for a Wasserstein worst case. It is not an exact DRO solve, and λ̃ is not renormalized, so it reads as an annual event rate.

**Change from submission.** Jamaica's BTM backup was changed from 100 to 84 MWh so that it matches the modeled BTM capacity. R(ε=0.2) moves from 0.98678 to 0.98664. The submitted manuscript quoted 0.970, which the code never produced; the revision reports 0.987.

**Calibration to-do.** Fit g_c and h_c to JPS / T&TEC restoration records (e.g., Beryl 2024, Melissa 2025).
