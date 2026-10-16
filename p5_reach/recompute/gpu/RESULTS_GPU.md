# P5 recompute, GPU units R_P4B and R_P3: results (campaign-record entries 146 registration, 147-148 raw, 149 decision)

MACE-MPA-0 medium in place of MACE-MP-0 small, same scripts, seeds and
protocol. CHPC notchpeak-gpu-guest: R_P4B 16172247 (2 points, 23.5 h and
25.2 h on one A6000-class node), R_P3 16172248 (89 of 89 runs completed, no
lost run). Raw outputs were hashed onto the campaign record before any analysis.

| Claim | Class predicted | Observed | Scored |
|---|---|---|---|
| C10 party-4b offset (MACE / Tersoff, same box) | magnitude only, rises to 0.7-1.0 | 0.55 / 0.58 -> 0.715 (x = 0.5) / 0.729 (x = 0.15) | held, magnitude hit |
| C11 composition trend kappa(0.15)/kappa(0.5) | magnitude only, 1.5-2.1 | 1.81 -> 1.74 (Tersoff 1.71) | held, magnitude hit |
| C12 head-to-head picks at 1100 K | decision may flip | pipeline 0.45 and every MF-GP pick unchanged; MF-BO replay ends at the same pick | held (over-predicted) |
| C13 P3 Q1 (covering vs random) | decision may flip | still refuted: CA1 0.164 vs random median 0.132 | held (over-predicted) |
| C14 P3 Q2 (one-factor-at-a-time worse) | decision may flip | still holds: 0.161 vs 0.140 | held (over-predicted) |
| C15 P3 Q3 (factor ranking) | decision may flip | same full ranking: Ge, T, carbon content, dopant, carbon form | held (over-predicted) |
| C16 P3 Q4 (dispersed vs clustered carbon) | decision may flip | ratio 0.992 -> 0.989 | held (over-predicted) |
| C17 P3 Q5 (carbon-free minimum) | magnitude only | x = 0.5 | held |
| C18 cost inputs | magnitude only | cost per point 4.1 h (GB10, cuEquivariance) -> 23.5-25.2 h (A6000, plain torch), about 8 h hardware-matched; no batch decision changes (below) | held |
| C19 planted fault P08 | magnitude only | Pr1-Pr7 read no P08 trial; P08 rerun at the recalibrated magnitude (kappa ratio 0.70-0.75, MPA lattice) still detected 50/50 | held |

Decision (gpu_design.json rule): all ten claims hold; campaign-record entries 149
`strengthen`, the claims now rest on two checkpoints. No flip, no paper text
change needed.

Reach scoring (PREDICTION.md section 6): 0 misses, 5 over-predictions (C12
to C16, the "decision may flip" items, all held).

Readings beyond the claims:
- **Level shift**: MPA-0 kappa is higher than MP-0 on the P3 recipes by a
  median factor 1.24 (range 0.91-1.59 over 89 runs), the same direction as
  the party-4b offset (MP-0 force noise suppresses kappa).
- **Prediction accuracy fell for every design**: hidden-recipe log RMSE
  CA1 0.119 -> 0.164, CA2 0.090 -> 0.174, OFAT 0.117 -> 0.161, random pool
  0.076 -> 0.121; replicate-seed differences are similar (0.08-0.13 both
  times). The design comparisons keep their verdicts because every design
  moved together; the absolute surrogate error reported in P3 is model
  dependent and should carry the model name.
- **C18 detail**: party-regime covering (p3_prework/covering) at 541 and
  1459 min per MACE point gives assignments identical to a same-code control
  at 246 min; only totals grow (base scenario optimum 24.5 h -> 34.3 h /
  64.9 h). SiGeC simulation covering (p3_limits): greedy batches identical in
  40 of 40 cases; the integer-program batches change identity but are
  co-optimal under the old weights (2864 / 5276 min) with the same number of
  MACE-checked (8 / 16) and 1100 K (6 / 12) runs, so the change is solver
  tie-breaking.
- **Side finding**: the committed `p3_prework/covering/results.json` (base
  optimum 41.4 h) is not what the current code and evidence graph produce
  (24.5 h at the same 246 min); it predates the hypergraph rebuilds. Not
  changed here; a rerun of `covering.py` refreshes it.

Scripts (all run code unchanged except the stated constant or input swap):
`rerun_h2h_mpa.py`, `rerun_cost_mpa.py`, `rerun_simcost_mpa.py`,
`rerun_p08_mpa.py`, `apply_gpu_mpa.py`; the P3 analysis is
`p3_mace/analyze_p3_mace.py` with `P3M_OUT=gpu/p3/out` (output moved to
`analysis/p3_mpa_results.json`). The head-to-head rerun used `--no-pysr`
(the pooled-SR rows were not recomputed; no claim reads them).
