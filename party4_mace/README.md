# Party 4b: MACE foundation-potential MD (hybrid-parentage party)

The pilot half of evidence party 4 (`../06_evidence_party_roadmap.md`),
executed on the DGX on 2026-09-27. Party id
`MACE-MD`. The point of this party: both existing MD parties share one
Tersoff potential (one textbook); MACE-MP carries a *different* textbook
(distilled Materials Project PBE DFT), so cross-party disagreement now
measures method-family bias instead of assuming it.

**Hybrid parentage, stated up front:** an ML foundation potential is MD
executed on distilled DFT. The party is therefore only half independent
of a future DFT+BTE party (4a), and its provenance records
`parentage: MACE-MP <- MP PBE DFT`. That is not a weakness to hide; it
is the exhibit the roadmap wanted, and the fitted law's per-term scope
labels can now distinguish "Tersoff-family evidence" from
"PBE-family evidence".

## Environment (DGX, aarch64 + GB10)

`~/venvs/mace`: torch 2.14.0+cu130 (CUDA works natively on the GB10,
no emulation), mace-torch 0.3.16, ase 3.29.0, cuEquivariance (3.7x:
434 -> 116 ms/step at 3072 atoms, mace-mp small, float32).

## Validation gate (`validate_mace.py` -> `validation_mace.json`)

| check | MACE-MP small | PBE reference | experiment |
|---|---|---|---|
| Si a0 | 5.464 A | ~5.47 | 5.431 |
| Ge a0 | 5.736 A | ~5.76 | 5.657 |
| Si e_coh | 4.36 eV | 4.55 | 4.63 |
| Ge e_coh | 3.47 eV | 3.71 | 3.85 |
| Si0.5Ge0.5 a0 vs Vegard | -0.105% | - | - |

Reading: lattice constants land on the PBE values, not the experimental
ones, which *confirms* the parentage story (the gate tests proximity to
the party's actual training distribution). Cohesive energies sit 4-7%
below the PBE references, the known softness of the small model; the
gate passes for MD purposes with that bias recorded as party metadata.

## Cross-check campaign (`mp_rnemd_ase.py`)

ASE Muller-Plathe rNEMD mirroring the Phase B protocol (4x4x24 cells,
3072 atoms, 20 slabs, swap every 50 steps, 20k equil + 130k prod at
1 fs, same-species swaps so the two-mass alloy conserves energy and
momentum exactly). Two points, sequential on the GPU (~5 h each):
x=0.5/300 K and x=0.15/300 K, chosen because all other parties cover
them (Tersoff DGX/CHPC, GPUMD HNEMD at x=0.5, literature, and the
database party at x=0.2).

**Collected 2026-09-27: see `RESULTS.md`.** The campaign
arrived with a unit slip (kappa inflated by exactly 1/units.fs^2 =
103.6427, one line in `mp_rnemd_ase.py`, since fixed); the raw outputs
are archived under `raw/`, the corrected ingestion copies under
`results/` (picked up by `../pilot/kg/extract_kg.py` as party
`MACE-MD`), and the correction is ledgered as a `correct` shard
operation on `../phase_c/ledger_campaign.jsonl`.

Fidelity: single seed, single box; trend/cross-check evidence, exactly
like the DGX Tersoff pilot points. Production party-4 numbers belong to
CHPC (`mace-lmp` module and/or party 4a almaBTE; `../party4_bte/`).
