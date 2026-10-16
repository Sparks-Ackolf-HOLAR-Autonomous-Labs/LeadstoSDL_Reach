# P5 recompute, unit R_Z1: results (campaign-record entries 133 registration, 137 raw, 138-139 decisions)

19 relaxations (1 reference + 18 Ge positions around an embedded SiC particle in a
pure Si host, one Ge atom placed per task; corrected 2026-10-11, the earlier text said
Si0.8Ge0.2, but `z1/mace_zone.py` builds a Si host) with MACE-MPA-0 medium (float64), CHPC notchpeak-guest 16163393
then 16163394, about 31 min for the reference and 4-8 min per position. Gate G1
(force and pressure) passes on every task. The committed Z1 analysis
(`nano_sigec/si_zone/analyze_zone.py`) was run unchanged; only the input path
was swapped (`summarize_z1_mpa.py`, output `zone_mpa_results.json`).

Energy of a Ge atom at distance d from the particle centre, relative to the far
matrix (eV; negative = Ge attracted):

| d (A) | MACE-MP-0 | MACE-MPA-0 | shift |
|---|---|---|---|
| 6.5 | -0.091 | +0.010 | +0.102 |
| 7.5 | -0.066 | -0.041 | +0.024 |
| 8.5 | +0.001 | -0.160 | -0.161 |
| 9.5 | -0.002 | +0.012 | +0.014 |
| 10.5 | +0.008 | +0.006 | -0.002 |
| 11.5 | -0.020 | -0.027 | -0.007 |
| 12.5 | -0.017 | -0.023 | -0.007 |
| 13.5 | -0.008 | +0.011 | +0.019 |

| Claim | Predicted at campaign-record entries 130 | Observed | Scored | Decision |
|---|---|---|---|---|
| C8: SiC attracts Ge in the first shell (PrZ1 refuted) | decision may flip; attraction holds, -0.25 to -0.02 eV, P(flip) 0.3 | +0.010 eV, above the +0.01 eV flip threshold by 0.4 meV | flipped (the record flagged it as at risk); magnitude outside the predicted band | campaign-record entries 138: scope_limit to MACE-MP-0 only; P1 and P2 sentences flagged in source, text unchanged at this step |
| C9: no equilibrium Ge-depleted zone, carbon claims stand | magnitude only; branch stays strengthen | w_eq = 0 A at 1473 K under both; cancel 0.00 at R = 2.5 and 5 nm | held as predicted | campaign-record entries 139: strengthen |

Reading:
- The materials decision (no Ge-depleted zone forms, so the zone does not
  cancel the carbon benefit) holds under both checkpoints. Under MACE-MPA-0
  the net Ge segregation is still towards the particle, so the zone is, if
  anything, Ge-enriched.
- What changed is where the attraction sits: first shell neutral, a
  stronger well (-0.16 eV) one shell further out at 8.5 A. The single
  first-shell verdict was a near-threshold quantity (0.09 eV against a
  version shift of about 0.1 eV here and 0.65-0.75 eV on dE_prec in R_M1C),
  and the reach file had marked it as one of the nine 'decision may flip'
  items. It is the only one of those nine that flipped so far.
- The flip margin (0.4 meV) is far below any physical resolution of either
  model; the registered rule decides it anyway, which is the point of a
  registered rule. A follow-up, if wanted, would read the profile as a whole
  (sum over shells) instead of the first shell alone; that needs its own
  registration.
