# Raw as-produced party 4b outputs (DO NOT USE THESE KAPPA VALUES)

These are the untouched outputs of the detached DGX campaign
(`~/mat_theory_party4/`, launched earlier, collected earlier).
The `kappa_W_mK` values in these JSONs are **wrong by exactly a factor
of 1/units.fs^2 = 103.6427**: the final unit conversion in
`mp_rnemd_ase.py` divided by `units.fs` where it should have
multiplied when converting a per-ASE-time rate to per-fs. Everything
upstream of that single line (structures, dynamics, swap bookkeeping,
temperature profiles, gradients) is unaffected; the per-swap
transferred energies recovered from these files (0.06-0.09 eV) are
physically sensible, so the runs themselves are good.

The corrected values live in `../results/` (the copies the evidence
hypergraph ingests), and the correction is recorded on the campaign
campaign record as a `correct` shard operation
(`phase_c/correct_mace_units_2026-09-27` op id; see
`../../phase_c/correct_mace_units.py`). Per the archive-keeping rule,
these raw files are retained unmodified as the evidence the correction
points back to; they must never be silently edited.
