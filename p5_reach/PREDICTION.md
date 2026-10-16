# P5 revision event 1: predicted reach of a MACE version change (9 October 2026)

Issue 55, P5 stage 1 (prediction only). Operator request: predict the reach
of the revision from the record before any recomputation. No MACE
calculation was run; `predict_reach.py` reads the ledger and committed
result files and finishes in under a second. Full output:
`reach_prediction.json`. Ledger read: 128 entries (sequence 0 to 127).

## 1. The event

Every MACE calculation in the campaign is repeated with a newer foundation
potential trained on more data (for example MACE-MPA-0, trained on MPtrj
plus Alexandria, or MACE-OMAT-0). The record holds two checkpoints, not
one. MACE-MP-0 medium in double precision was used for the where-carbon-goes
relaxations (M1, M1c) and the Si-zone segregation profile (Z1). MACE-MP-0
small in single precision was used for the party-4b and P3 molecular
dynamics. No file names the checkpoint file itself; the design files name
"MACE-MP-0 medium" and the CHPC module `mace/0.3.16_cu126`. A version change
therefore also changes model size for the MD runs, unless a small variant
of the new model is used.

## 2. What a potential version change can alter in the SiGeC conclusions

A foundation potential sets three things that the campaign used.

- **Energies of competing atomic arrangements.** Whether a carbon atom on
  a Si or Ge lattice site gains energy by leaving to form a SiC precipitate,
  which neighbour shells it prefers, and whether a SiC particle attracts or
  repels Ge. These are energy differences of 0.1 to 1.7 eV. A newer model
  moves them by an amount the record bounds at about 0.3 eV (the boundary
  of the registered O3 categories, ledger 122 to 123).
- **Lattice constants.** MACE-MP-0 inherits the PBE overestimate of the Ge
  lattice constant (+2.0% against a 2.5% gate). A newer model trained on
  PBE-family data keeps this offset in kind but not in size.
- **Phonon stiffness and force noise.** These set the MD thermal
  conductivity. Universal potentials are softer than DFT, and later,
  larger training sets reduce that softening (Deng et al., npj Comput.
  Mater. 2025). The party-4b offset (MACE at 0.55 to 0.58 times Tersoff)
  is the measured size of this effect for the old checkpoint.

Alloy mass-disorder scattering, which drives the composition dependence of
SiGe conductivity, depends on the Si and Ge masses and not on the potential.
Conclusions that rest on it are predicted to hold.

## 3. Reach: explicit links versus inferred links

Seeds: the six ledger entries that commit MACE output (1, 47, 54, 69, 72,
and 126 for the P4 T1 GeSn run now in progress), plus MACE-derived constants
copied into code with no ledger entry of their own (the P08 fault magnitude,
the detector-v2 lattice ratio, and the MACE cost weights in the P3 cost
model).

| Links allowed | Ledger entries reached (of 128) |
|---|---|
| explicit sequence fields and named op_ids only | 8 |
| plus free-text citations ("ledger seq 61") | 13 |
| plus file paths to code that reads MACE results | 31 |
| plus shared or parent campaign names | 49 |

Beyond the ledger, 7 figure scripts of P1 read MACE outputs directly, and
105 lines of the P1 to P3 drafts either name MACE (65) or cite a reached
ledger entry (40).

**P5 finding.** The explicit links reach 8 entries, and four of these are
seeds or their immediate successors. Most of the dependence passes through
two routes that the ledger does not record: free text, and shared analysis
code. One script, `nano_sigec/analyze_sigec.py`, loads the converged MACE
summary for every SiGeC analysis (light dopants, small-SiC MD, P3 design
study, second system). The constants route has no ledger trace at all.
One parent-campaign name (`nano-sigec-2026-09-29`, ledger 58) matches no
campaign. Making `rests_on` mandatory and recording the analysis-code hash
would close most of the gap.

## 4. Predicted sensitivity of each reached claim

Of 24 claims: 9 may change their decision, 9 change in magnitude only, and
6 are unaffected. Each prediction below can be refuted by the recompute.

### Decision may flip

| Claim (ledger) | Margin in the record | Prediction | Refuted if |
|---|---|---|---|
| Lattice gate M1c-c that lifted the 'unvalidated' flag on the carbon energies (53 to 55) | Ge +2.04% vs 2.5% gate: 0.46 percentage points | gate passes (stated probability of failure about 0.3) | Ge more than 2.5% above 5.658 A (the strengthen of ledger 55 reverts), or below +1.5% |
| Carbon precipitation more favourable at x = 0.5 than x = 0, PrC2 trend part (49, 55) | difference 0.24 eV, inside the 0.3 eV band | holds | dE_prec(0.5) >= dE_prec(0) |
| Carbon prefers Si-rich shells, PrC2b (49, 55); motivated the Si-rich pocket in the small-SiC MD (58) | 0.21 eV at x = 0.2 | holds at both x | dE_site <= 0 at x = 0.2 or 0.5 |
| PrZ1 verdict: SiC attracts Ge at 6.5 A (69, 70, 121) | -0.091 eV | attraction holds (stated probability of a flip about 0.3) | dE(6.5 A) > +0.01 eV |
| Head-to-head baseline rows using the two MACE points as middle fidelity: MF-GP pick and the multi-fidelity BO replay (63, 66, 67) | 1100 K minimum flat over x = 0.35 to 0.60 within 8%; MF-GP pick moved 0.50 to 0.40 when only the MACE level changed | pipeline row unchanged; an MF-GP pick moves by at most 0.05 | pipeline row changes, or an MF-GP pick moves by more than 0.10 |
| P3 Q1 refuted: covering 15 no better than random 15 on hidden MACE-MD (72, 73) | log RMSE margin 0.032, below the seed noise 0.083 | stays refuted while carbon and dopant stay below seed noise | covering 15 at or below the random median |
| P3 Q2 holds: one-factor-at-a-time worse than random (72, 73) | margin 0.022 | holds | OFAT at or below the random-12 median |
| P3 Q3 refuted: dopant ranked 4th, not last (72, 73) | the last three importances are all below noise | Ge content first, temperature second; last three reorder about half the time | Ge content not first |
| P3 Q4: dispersed carbon lower than clustered, ratio 0.992 (72, 73) | 0.008 below the threshold | ratio within 0.95 to 1.05 | ratio outside 0.95 to 1.05 |

### Magnitude only

- **Carbon leaves the lattice** (PrC2 sign part; P1 headline): dE_prec =
  -1.44, -1.55, -1.68 eV at x = 0, 0.2, 0.5. The margin is 0.94 eV to the
  registered -0.5 eV threshold and 1.44 eV to a sign change, against a
  plausible shift of about 0.3 eV. Refuted if dE_prec rises above -0.5 eV
  at any x.
- **Recipe pick x = 0.3, 3 at% C as few-nm SiC.** The equilibrium
  constraint reads only the sign of dE_prec. The unconstrained pick is
  already a SiC form (PrC3), and the recorded contrast sweep left the pick
  unchanged over the whole contrast range. Refuted if any pick changes.
- **Size misfit delta_C**: within 6% of the modified-Vegard fallback the
  design already carries. Replacing it moved one upper bound by 1.4%.
- **Si-rich zone decision** (cancel < 0.2): replaying the registered
  formula, full Ge depletion of the two bins that carry signal (closer than
  8 A) gives a zone of only 2.0 A (cancel 0.04). A flip needs a uniform
  repulsion of 0.19 eV at every distance out to 13.5 A. Segregation
  energies are differences against far sites, so a uniform far-field shift
  is the implausible case. Refuted if cancel reaches 0.2, or if |dE| reaches
  0.1 eV beyond 9 A.
- **Party offset 0.55 to 0.58 times Tersoff**: predicted to rise towards
  0.7 to 1.0 (less softening). Refuted if it falls below 0.55.
- **Composition trend across methods** (ratio 1.81 vs Tersoff 1.71):
  predicted within 1.5 to 2.1.
- **P3 Q5** (carbon-free minimum at x = 0.5): predicted in [0.3, 0.7].
- **Cost inputs and the P08 planted fault**: re-reported, not re-decided.
  No registered prediction of detector v2 reads P08.

### Unaffected

The Ge saving at equal conductivity (13.7 to 16.2% at R = 2.5 nm, ledger
105 and 110) rests on Tersoff particle MD and almaBTE modes, so it is
predicted identical to the last digit. Also unaffected: light dopants
(74 to 76), records with no MACE quantity (60, 71), the fault-study chain
(5, 6, 14, 24, 83), and the P4 T1 run (126, 127), which has no result yet.
The P4 T1 benchmarks already show the lattice offset (a0 = 5.92 A against
Vegard 5.76 A for Ge0.88Sn0.12). The AI-theorist answers to O3 are
predictions about this recompute, which will grade them.

## 5. Minimal recompute set

All nine 'decision may flip' items are settled by four units. Costs are the
recorded wall times of the old checkpoints.

| Unit | What | Recorded cost | Settles |
|---|---|---|---|
| R_M1C | 51 relaxations (bulk Si, Ge, 3C-SiC; hosts x = 0, 0.2, 0.5 with 0 to 4 C; min/max-Ge shells), float64, same gates | 1.75 CPU-task-h (16-core guest) | lattice gate, carbon trend, shell preference, O3 |
| R_Z1 | 19 Ge-segregation relaxations around a SiC sphere | 2.93 CPU-task-h | PrZ1, zone decision |
| R_P4B | 2 party-4b MD points, then the head-to-head script (seconds) | 8.1 GPU-h (GB10) | MF-GP rows, party offset |
| R_P3 | all 89 P3 MD runs (Q3 needs all 71 planner points) | 150 GPU-h (guest GPUs) | Q1 to Q4 |

Total: 4.7 CPU-task-h and 158 GPU-h. Suggested order: the two CPU units
first, because they settle five of the nine items, including the lattice
gate. A 6-run screen (repeat-seed pairs plus matched carbon-form pairs,
about 10 GPU-h) can come before R_P3. If the new seed noise and carbon
contrast both stay below noise, Q3 and Q4 are predicted to remain
uninformative. P3 and party 4b used the small single-precision model, so a
medium-size newer model will cost more per step. Measure the cost with one
timing run before submitting. Each unit runs longer in total than the 1000 s session wait
limit, so all four are submitted detached and collected in a later
session.

## 6. Scoring rule for H5a

After the recompute, each claim is scored as predicted or missed. Misses
are affected items that were predicted unaffected or magnitude only; an
over-prediction is a 'decision may flip' item whose decision held. The
reach sets in section 3 are scored the same way. An entry whose output
changes but which lies outside the 49 reached entries is a miss of the
graph.
