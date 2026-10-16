#!/usr/bin/env python3
"""Party 4b validation gate: MACE foundation potential vs the known Si/Ge
anchors, same discipline as the Phase B LAMMPS gate and the GPUMD gate.

Checks (targets from the Phase B validation, experiment in parentheses):
- Si diamond lattice constant  a0 ~ 5.43 A
- Ge diamond lattice constant  a0 ~ 5.66 A
- Si cohesive energy           ~ 4.6 eV/atom (expt 4.63)
- Ge cohesive energy           ~ 3.9 eV/atom (expt 3.85)
- Si0.5Ge0.5 random-alloy lattice constant vs Vegard

Note the systematic caveat recorded in advance: MACE-MP is trained on
PBE data, and PBE cohesive energies differ from experiment (Si PBE
~4.55, Ge PBE ~3.7 eV/atom). The gate therefore tests proximity to the
PBE-DFT values, because that is the party's actual parentage; the gap
to experiment is *inherited bias the provenance layer must carry*, not
a validation failure. That is the hybrid-parentage exhibit the roadmap
wanted from party 4b.

Run:  ~/venvs/mace/bin/python validate_mace.py [--model small|medium]
Out:  validation_mace.json next to this script.
"""
import argparse
import json
import random
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.eos import EquationOfState
from ase import Atoms

HERE = Path(__file__).resolve().parent


def eos_a0(calc, sym_or_atoms, a_guess):
    energies, volumes = [], []
    for s in np.linspace(0.98, 1.02, 9):
        if isinstance(sym_or_atoms, str):
            at = bulk(sym_or_atoms, "diamond", a=a_guess * s, cubic=True)
        else:
            at = sym_or_atoms.copy()
            at.set_cell(sym_or_atoms.cell * s, scale_atoms=True)
        at.calc = calc
        energies.append(at.get_potential_energy())
        volumes.append(at.get_volume())
    eos = EquationOfState(volumes, energies, eos="sj")
    v0, e0, _ = eos.fit()
    n = len(at)
    return (v0 / (n / 8)) ** (1 / 3), e0 / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    args = ap.parse_args()
    from mace.calculators import mace_mp
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    calc = mace_mp(model=args.model, device=device, default_dtype="float64")

    out = {"model": f"mace-mp {args.model}", "device": device,
           "parentage": "MACE-MP foundation model, trained on Materials "
                        "Project PBE DFT data (hybrid parentage: this "
                        "party is MD executed on distilled DFT)"}

    for sym, a_guess, pbe_ecoh, expt_ecoh in (("Si", 5.43, 4.55, 4.63),
                                              ("Ge", 5.66, 3.71, 3.85)):
        a0, e_bulk = eos_a0(calc, sym, a_guess)
        atom = Atoms(sym, cell=[18, 19, 20], pbc=True)
        atom.calc = calc
        e_atom = atom.get_potential_energy()
        out[sym] = {"a0_A": round(a0, 4),
                    "e_coh_eV": round(e_atom - e_bulk, 4),
                    "pbe_ref_e_coh": pbe_ecoh, "expt_e_coh": expt_ecoh}

    # random Si0.5Ge0.5, 64 atoms, Vegard guess
    random.seed(55)
    a_veg = 0.5 * out["Si"]["a0_A"] + 0.5 * out["Ge"]["a0_A"]
    cell = bulk("Si", "diamond", a=a_veg, cubic=True) * (2, 2, 2)
    syms = ["Si"] * 32 + ["Ge"] * 32
    random.shuffle(syms)
    cell.set_chemical_symbols(syms)
    a0_alloy, _ = eos_a0(calc, cell, a_veg)
    out["Si0.5Ge0.5"] = {"a0_A": round(a0_alloy, 4),
                         "vegard_A": round(a_veg, 4),
                         "dev_pct": round(100 * (a0_alloy / a_veg - 1), 3)}

    (HERE / "validation_mace.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
