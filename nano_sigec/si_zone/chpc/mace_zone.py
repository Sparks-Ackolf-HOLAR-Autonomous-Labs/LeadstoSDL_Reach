#!/usr/bin/env python3
"""Si-depleted zone check, stage Z1 (zone_design.json): how strongly does an
embedded 3C-SiC particle push Ge away from itself in Si?

Task 0 relaxes the reference cell (Si host, NREP^3 diamond cells, one 3C-SiC
sphere of radius RP at the centre, host atoms within DOV of a particle atom
deleted). Tasks 1..N start from the relaxed reference, turn ONE host Si atom
at a chosen distance d from the particle centre into Ge, and relax again.
Delta E(d) = E(Ge at d) - mean E(Ge at the two farthest sites) is the Ge
segregation energy profile (dilute limit). Checkpointed for guest preemption.
Usage: mace_zone.py <task_index> [--build-only]"""
import json, os, sys, time
import numpy as np
from ase import Atoms
from ase.build import bulk
from ase.filters import FrechetCellFilter
from ase.io import read, write
from ase.optimize import FIRE, LBFGS
from ase.units import GPa

NREP, RP, DOV = 6, 5.0, 1.6
A_SI, A_SIC = 5.431, 4.36
DBINS = [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5]
FGATE, PGATE, CAP, S1CAP = 0.01, 0.1, 5000, 800


def build_reference():
    host = bulk("Si", "diamond", a=A_SI, cubic=True).repeat((NREP,) * 3)
    c = host.cell.diagonal() / 2
    d = np.linalg.norm(host.positions - c, axis=1)
    host = host[d > RP]
    sic = bulk("SiC", "zincblende", a=A_SIC, cubic=True).repeat((4, 4, 4))
    sic.positions += c - sic.cell.diagonal() / 2
    ds = np.linalg.norm(sic.positions - c, axis=1)
    sic = sic[ds <= RP]
    dd = np.linalg.norm(host.positions[:, None, :] - sic.positions[None, :, :], axis=2).min(axis=1)
    host = host[dd >= DOV]
    atoms = Atoms(list(host.get_chemical_symbols()) + list(sic.get_chemical_symbols()),
                  positions=np.vstack([host.positions, sic.positions]), cell=host.cell, pbc=True)
    tags = np.array([0] * len(host) + [1] * len(sic))  # 0 host, 1 particle
    atoms.set_tags(tags)
    return atoms


def site_list(ref):
    """Deterministic Ge sites: for each distance bin, the two host Si atoms
    closest to the bin centre whose directions from the particle centre differ
    by more than 60 degrees; plus the two farthest host atoms (references)."""
    c = ref.cell.diagonal() / 2
    host = np.where(ref.get_tags() == 0)[0]
    v = ref.positions[host] - c
    v -= ref.cell.diagonal() * np.round(v / ref.cell.diagonal())
    r = np.linalg.norm(v, axis=1)
    inside = r < ref.cell.diagonal().min() / 2 - 0.5
    sites = []
    for b in DBINS:
        order = np.argsort(np.abs(r - b))
        pick = []
        for k in order:
            if not inside[k]:
                continue
            if all(np.dot(v[k], v[j]) / (r[k] * r[j]) < 0.5 for j in pick):
                pick.append(k)
            if len(pick) == 2:
                break
        sites += [(f"d{b}_{i}", int(host[k]), float(r[k])) for i, k in enumerate(pick)]
    far = [k for k in np.argsort(-r) if inside[k]]
    far2 = [far[0]] + [k for k in far[1:] if np.dot(v[far[0]], v[k]) / (r[far[0]] * r[k]) < 0.5][:1]
    sites += [(f"far_{i}", int(host[k]), float(r[k])) for i, k in enumerate(far2)]
    return sites


def relax(atoms, task, state_dir):
    from mace.calculators import mace_mp
    ck, st = f"{state_dir}/{task}.extxyz", f"{state_dir}/{task}.state.json"
    state = {"steps": 0, "stage": 1, "wall_s": 0.0, "restarts": 0}
    if os.path.exists(ck) and os.path.exists(st):
        prev = read(ck)
        assert list(prev.get_chemical_symbols()) == list(atoms.get_chemical_symbols())
        tags = atoms.get_tags(); atoms = prev; atoms.set_tags(tags)
        state = json.load(open(st)); state["restarts"] += 1
    atoms.calc = mace_mp(model="medium", default_dtype="float64", device="cpu")
    filt = FrechetCellFilter(atoms, hydrostatic_strain=True)
    t0 = time.time()

    def save():
        write(ck, atoms)
        json.dump({**state, "wall_s": state["wall_s"] + time.time() - t0}, open(st, "w"))

    def run(opt, fmax, cap):
        while state["steps"] < cap:
            n0 = opt.nsteps
            done = opt.run(fmax=fmax, steps=min(25, cap - state["steps"]))
            state["steps"] += opt.nsteps - n0
            save()
            if done or opt.nsteps == n0:
                return bool(done)
        return False

    if state["stage"] == 1:
        run(FIRE(filt, logfile=None), 0.05, S1CAP)
        state["stage"] = 2; save()
    conv = run(LBFGS(filt, maxstep=0.1, logfile=None), 0.005, CAP)
    f = float(np.linalg.norm(atoms.get_forces(), axis=1).max())
    p = float(-np.trace(atoms.get_stress(voigt=False)) / 3 / GPa)
    return atoms, {"E_eV": float(atoms.get_potential_energy()), "V_A3": float(atoms.get_volume()),
                   "fmax_norm": f, "pressure_GPa": p, "optimizer_converged": conv,
                   "steps": state["steps"], "restarts": state["restarts"],
                   "gate_pass": bool(f <= FGATE and abs(p) <= PGATE),
                   "wall_s": state["wall_s"] + time.time() - t0}


def main(i, build_only=False):
    os.makedirs("out", exist_ok=True); os.makedirs("ckpt", exist_ok=True)
    if i == 0:
        atoms = build_reference()
        nC = int(sum(s == "C" for s in atoms.get_chemical_symbols()))
        meta = {"task": "ref", "n_atoms": len(atoms), "n_C": nC,
                "n_particle": int(atoms.get_tags().sum()), "RP_A": RP, "NREP": NREP}
        if build_only:
            print(json.dumps(meta)); return atoms
        atoms, res = relax(atoms, "ref", "ckpt")
        write("out/ref_relaxed.extxyz", atoms)
        json.dump({**meta, "model": "MACE-MP-0 medium float64", **res}, open("out/ref.json", "w"), indent=1)
        return
    ref = read("out/ref_relaxed.extxyz")
    tags = build_reference().get_tags()
    assert len(tags) == len(ref); ref.set_tags(tags)
    name, idx, r0 = site_list(ref)[i - 1]
    s = ref.get_chemical_symbols(); assert s[idx] == "Si"; s[idx] = "Ge"
    ref.set_chemical_symbols(s)
    atoms, res = relax(ref, name, "ckpt")
    json.dump({"task": name, "site_index": idx, "d_A": r0, "model": "MACE-MP-0 medium float64", **res},
              open(f"out/{name}.json", "w"), indent=1)
    print("done", name, res["gate_pass"], res["fmax_norm"], res["steps"])


if __name__ == "__main__":
    main(int(sys.argv[1]), "--build-only" in sys.argv)
