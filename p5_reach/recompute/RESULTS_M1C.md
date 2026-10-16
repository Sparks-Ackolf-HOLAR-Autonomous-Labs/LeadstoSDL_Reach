# P5 recompute, unit R_M1C: results (campaign-record entries 133 registration, 134 raw, 135 decision)

51 relaxations with MACE-MPA-0 medium (float64), CHPC notchpeak-guest array
16163392, about 4 minutes wall time for the whole array. All converged
(max force 0.005 eV/A, max |pressure| 0.04 GPa, at most 78 steps).

| Quantity | MACE-MP-0 | MACE-MPA-0 | Predicted at campaign-record entries 130 | Scored |
|---|---|---|---|---|
| Ge lattice error (gate 2.5 %) | +2.04 % | +1.08 % | gate passes, +1.5 to +2.5 % | decision held; magnitude miss (better than predicted) |
| Si, 3C-SiC lattice error | +0.45 %, +0.37 % | +0.67 %, +0.61 % | | |
| Carbon gain on forming SiC, x = 0 / 0.2 / 0.5 (eV per C) | -1.44 / -1.55 / -1.68 | -2.08 / -2.27 / -2.43 | sign holds, shift 0.05-0.3 eV | decision held; magnitude miss (shift 0.65-0.75 eV) |
| Trend with Ge, x = 0.5 minus x = 0 | -0.24 eV | -0.35 eV | holds, 0.1-0.4 eV | held (over-predicted as may-flip) |
| C prefers Si-rich shells, x = 0.2 / 0.5 | 0.21 / 0.33 eV | 0.24 / 0.39 eV | holds, 0.1-0.4 eV | held (over-predicted) |
| Carbon size misfit delta_C | -0.40 / -0.41 / -0.37 | -0.35 / -0.35 / -0.34 | within 10 % of -0.394 | not refuted (within 30 % of Vegard); magnitude miss |

Reading:
- No decision flipped. Three of the nine "decision may flip" items are now
  settled, and all three held: the reach prediction over-predicted risk on
  them. Every claim now rests on two checkpoints (campaign-record entries 135, strengthen).
- The record's assumed size of a version change (0.3 eV) was too small by a
  factor of about 2.5 on the precipitation energy. The decisions held only
  because their margins (0.94 eV to threshold) were large. For P5 this is
  the main finding of the unit: the decision-level reach was right or
  conservative, the magnitude-level prediction was not.
- O3 (AI theorists): outcome "sign holds, magnitude changes by more than
  0.3 eV". Theorist A (Sonnet) right in category (its value 1.3 eV is off),
  theorist B (Haiku) wrong, theorist C (Theorizer) gave no answer. The
  reach file's own guess (C20, B's category) is refuted.

Scored later: C6, C7, C21 held (campaign-record entries 142, `sigec_mpa/comparison.json`, from
an `analyze_sigec.py` rerun on this summary); C9 held and C8 flipped
(`RESULTS_Z1.md`, campaign-record entries 138-139, Z1 jobs 16163393 then 16163394); C19 is scored
with the GPU unit R_P4B.
