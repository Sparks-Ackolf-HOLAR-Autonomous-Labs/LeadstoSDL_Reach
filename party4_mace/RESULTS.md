# Party 4b results: MACE-MP rNEMD cross-check

Two-point campaign run detached on the DGX (GB10, cuEquivariance,
float32), collected 2026-09-27. Raw as-produced outputs are archived
unmodified under `raw/` (their kappa values are wrong; see below);
the corrected ingestion copies live under `results/` and are the ones
`pilot/kg/extract_kg.py` joins to the evidence hypergraph as party
`MACE-MD`. Run logs are not included.

## The unit slip, and the correct operation that fixed it

The campaign arrived with a pipeline fault of its own: raw kappa read
39.5 W/mK at x=0.5, which is physically impossible in a strongly
size-suppressed 4x4x24 box (the BTE-DFT *bulk* value at that
composition is 6.49 W/mK, and the same box under Tersoff reads
~0.7). The cause was one line in `mp_rnemd_ase.py`: converting the
kappa rate from per-ASE-time to per-fs requires multiplying by
`ase.units.fs`, and the script divided, inflating kappa by exactly
1/units.fs^2 = 103.6427. Verification that only that line was wrong:
the inflation factor matches to four decimals, and the per-swap
transferred kinetic energies recovered from the raw outputs (0.0621
and 0.0860 eV) are physically sensible, so the dynamics and
bookkeeping upstream are sound.

Handling followed the shard grammar exactly as designed. The error has
an identified cause, so under the two-bar rule this is a `correct`
operation, not a quarantine: raw values archived (never edited),
corrected values written alongside with the correction metadata
embedded, the one-line fix committed to both script copies, and the
operation ledgered on `phase_c/ledger_campaign.jsonl` (seq 1, op id
`correct-mace-units-2026-09-27`, chain verified). This is the first
*undesigned* correct operation of the campaign: nobody planted this
fault. It is P1 exhibit material for the same reason the Fe = 1e-4
GPUMD runaway is P2 exhibit material.

Detection lesson, now standing practice: a new party's first
datapoints get a cross-party sanity check against the physical bounds
the existing parties imply (here: a size-suppressed box must read
below the bulk value of any credible method family) before ingestion.

## Corrected numbers, against the other parties at the identical box

Protocol: identical to Phase B pilot fidelity, 4x4x24 cells (3072
atoms), 20 slabs, swap every 50 steps, 20k equil + 130k prod at 1 fs,
seed 101, Muller-Plathe rNEMD; same-species swaps (exact conservation
for the two-mass alloy). Single seed, single box: trend/cross-check
evidence, exactly like the DGX Tersoff pilot points.

| x_Ge | T (K) | MACE-MP (this) | Tersoff CHPC s101 | Tersoff seed band | Tersoff DGX | MACE/Tersoff(s101) |
|---|---|---|---|---|---|---|
| 0.5 | 300 | 0.3815 | 0.696 | 0.714 +/- 0.023 (4 seeds) | 0.744 | 0.55 |
| 0.15 | 300 | 0.6896 | 1.188 | - | 1.141 | 0.58 |

(kappa in W/mK; the Tersoff seed band is the Phase B 4-seed statistic
at x=0.5, z24.)

Readings:

1. **The composition physics agrees across method families.** Both
   parties order the compositions the same way and with nearly the
   same sensitivity: kappa(x=0.15)/kappa(x=0.5) is 1.81 under MACE and
   1.71 under Tersoff (CHPC s101). The alloy-scattering signal, which
   is the physics the fitted law lives on, is method-family-robust at
   this box.
2. **The absolute scale differs by a consistent ~1.8x factor**, MACE
   below Tersoff at both compositions (ratios 0.55 and 0.58). This is
   the measured same-protocol inter-party offset the roadmap wanted
   from party 4b. Direction and rough size are consistent with the
   known MLIP effect: force noise acts like artificial phonon
   scattering and *underestimates* kappa (Wu et al., J. Chem. Phys.
   2024, DOI 10.1063/5.0213811), and float32 inference adds force
   noise on top. So this offset should be read as party bias to be
   carried on MACE-MD scope labels, not as "the PBE family says kappa
   is lower": the PBE-family *bulk* statement belongs to party 4a
   (almaBTE), which reads 6.49 W/mK at x=0.5 against the Tersoff
   extrapolation of 1.80.
3. **Both parties are equally size-limited.** At one box there is no
   1/L extrapolation, so these are cross-check points, not fitting
   evidence; they populate regimes x0T0 and x2T0 in the hypergraph
   with a second MD textbook. The steep-gradient caveat from Phase B
   applies here too (slab profiles span ~105-486 K at x=0.5); Phase B
   measured that bias at only 3-5% for Tersoff, and the same
   gentler-swap check is the first follow-up if this party is ever
   promoted beyond pilot fidelity.
4. **Cost:** ~4.1 h per point on the GB10 (94.8 ms/step at 3072
   atoms) versus minutes for Tersoff: the measured ~50x cost ratio
   between the foundation-potential and empirical-potential parties,
   which is exactly the kind of number P3's cost-aware party-regime
   assignment consumes.

## What party 4b has delivered, in total

- Validation gate: MACE-MP lands on PBE lattice constants, not
  experimental ones (hybrid parentage made visible; see README).
- Same-protocol cross-check: composition trend confirmed across
  method families; consistent ~1.8x party offset measured (above).
- A live, undesigned `correct` shard operation with full campaign record trail.
- The measured cost ratio for planning.

Production party-4 numbers stay with CHPC (mace-lmp module and/or
party 4a almaBTE, which is collected; see `../party4_bte/RESULTS.md`).
