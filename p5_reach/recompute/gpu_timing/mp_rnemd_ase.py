#!/usr/bin/env python3
"""Party 4b cross-check point: Muller-Plathe rNEMD with the MACE
foundation potential, mirroring the Phase B LAMMPS protocol at pilot
fidelity, in ASE (no LAMMPS-MACE build needed on aarch64).

Protocol (matches chpc/in.mp_kappa where physics allows):
- diamond Si1-xGex random alloy, ncx x ncy x ncz conventional cells,
  Vegard lattice constant
- NVT (Langevin) equilibration, then NVE production with kinetic-energy
  swaps every `swap_every` steps between the cold slab (z=0) and the hot
  slab (z=L/2), 20 z-slabs
- swaps only between same-species atoms (hottest in cold slab vs coldest
  in hot slab), which conserves energy and momentum exactly for the
  two-mass alloy
- kappa = sum(transferred KE) / (2 A t dT/dz), gradient from the linear
  fit of the slab temperature profile over each half box, first 20% of
  production discarded

Fidelity note for the ledger: this is *trend/cross-check* evidence at
pilot fidelity (one seed, one box, shorter run than Phase B), party
MACE-MD. Production party-4 numbers come from CHPC (mace-lmp / almaBTE).

Run:  ~/venvs/mace/bin/python mp_rnemd_ase.py --x 0.5 --T 300 \
          --ncz 24 --equil 20000 --prod 130000 --out results/x05_T300.json
"""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.md.verlet import VelocityVerlet
from ase import units

NSLAB = 20


def build_alloy(x, ncx, ncy, ncz, seed):
    a = 5.431 * (1 - x) + 5.658 * x            # Vegard, same as Phase B
    at = bulk("Si", "diamond", a=a, cubic=True) * (ncx, ncy, ncz)
    rng = random.Random(seed)
    n = len(at)
    nge = round(x * n)
    idx = list(range(n))
    rng.shuffle(idx)
    syms = np.array(["Si"] * n)
    syms[idx[:nge]] = "Ge"
    at.set_chemical_symbols(syms.tolist())
    return at


def slab_of(at):
    z = at.get_positions()[:, 2] % at.cell[2, 2]
    return (z / at.cell[2, 2] * NSLAB).astype(int) % NSLAB


def slab_temps(at, slabs):
    v = at.get_velocities()
    m = at.get_masses()
    ke = 0.5 * m * (v ** 2).sum(axis=1)        # ASE internal units
    T = np.zeros(NSLAB)
    for s in range(NSLAB):
        sel = slabs == s
        # 3/2 kB T per atom
        T[s] = ke[sel].mean() * 2 / (3 * units.kB) if sel.any() else 0.0
    return T


def mp_swap(at, slabs):
    """One Muller-Plathe swap; returns transferred kinetic energy (eV)."""
    v = at.get_velocities()
    m = at.get_masses()
    ke = 0.5 * m * (v ** 2).sum(axis=1)
    syms = np.array(at.get_chemical_symbols())
    cold, hot = slabs == 0, slabs == NSLAB // 2
    best = None
    for sp in ("Si", "Ge"):
        ci = np.where(cold & (syms == sp))[0]
        hi = np.where(hot & (syms == sp))[0]
        if not len(ci) or not len(hi):
            continue
        i, j = ci[np.argmax(ke[ci])], hi[np.argmin(ke[hi])]
        gain = ke[i] - ke[j]
        if gain > 0 and (best is None or gain > best[2]):
            best = (i, j, gain)
    if best is None:
        return 0.0
    i, j, gain = best
    v[[i, j]] = v[[j, i]]
    at.set_velocities(v)
    return float(gain)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=float, required=True)
    ap.add_argument("--T", type=float, required=True)
    ap.add_argument("--ncx", type=int, default=4)
    ap.add_argument("--ncy", type=int, default=4)
    ap.add_argument("--ncz", type=int, default=24)
    ap.add_argument("--equil", type=int, default=20000)
    ap.add_argument("--prod", type=int, default=130000)
    ap.add_argument("--swap-every", type=int, default=50)
    ap.add_argument("--dt-fs", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from mace.calculators import mace_mp
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    at = build_alloy(args.x, args.ncx, args.ncy, args.ncz, args.seed)
    try:
        at.calc = mace_mp(model=args.model, device=device,
                          default_dtype="float32", enable_cueq=True)
    except Exception as e:                     # noqa: BLE001
        print("cueq unavailable, plain torch:", repr(e)[:80], flush=True)
        at.calc = mace_mp(model=args.model, device=device,
                          default_dtype="float32")
    slabs = slab_of(at)                        # solid: assignment is static
    area = at.cell[0, 0] * at.cell[1, 1]       # A^2
    lz = at.cell[2, 2]

    MaxwellBoltzmannDistribution(at, temperature_K=args.T)
    t0 = time.time()
    dyn = Langevin(at, args.dt_fs * units.fs, temperature_K=args.T,
                   friction=0.02)
    dyn.run(args.equil)
    print(f"equil done {time.time()-t0:.0f}s "
          f"({(time.time()-t0)/max(args.equil,1)*1e3:.1f} ms/step)",
          flush=True)

    nve = VelocityVerlet(at, args.dt_fs * units.fs)
    transferred, profiles, nprof = 0.0, np.zeros(NSLAB), 0
    discard = int(args.prod * 0.2)
    done = 0
    kelog = []
    while done < args.prod:
        nve.run(args.swap_every)
        done += args.swap_every
        gain = mp_swap(at, slabs)
        if done > discard:
            transferred += gain
            profiles += slab_temps(at, slabs)
            nprof += 1
            kelog.append(transferred)
        if done % 10000 == 0:
            print(f"prod {done}/{args.prod} {time.time()-t0:.0f}s",
                  flush=True)

    prof = profiles / max(nprof, 1)
    # gradient over each half, skipping the swap slabs themselves
    s = np.arange(NSLAB) + 0.5
    zpos = s * lz / NSLAB
    half1 = slice(1, NSLAB // 2)
    half2 = slice(NSLAB // 2 + 1, NSLAB)
    g1 = np.polyfit(zpos[half1], prof[half1], 1)[0]
    g2 = np.polyfit(zpos[half2], prof[half2], 1)[0]
    grad = (abs(g1) + abs(g2)) / 2             # K/A
    t_prod = (args.prod - discard) * args.dt_fs * units.fs
    flux = transferred / (2 * area * t_prod)   # eV / (A^2 * ASE-time)
    kappa_ase = flux / grad                    # eV / (A * ASE-time * K)
    # per-ASE-time -> per-fs MULTIPLIES by units.fs (1 ASE time unit
    # = 1/units.fs fs ~ 10.18 fs). The first campaign divided here,
    # inflating kappa by exactly 1/units.fs^2 = 103.6427; see
    # party4_mace/raw/README.md and the ledgered correct operation.
    # eV/(A fs K) -> W/(m K): 1 eV=1.602e-19 J, 1 A=1e-10 m, 1 fs=1e-15 s
    kappa = kappa_ase * units.fs * 1.602176634e-19 / 1e-10 / 1e-15

    out = {"x": args.x, "T": args.T, "kappa_W_mK": round(float(kappa), 4),
           "tag": f"mace_x{args.x}_T{args.T:.0f}_z{args.ncz}_s{args.seed}",
           "engine": f"ASE Muller-Plathe + mace-mp {args.model} ({device})",
           "natoms": len(at), "ncz": args.ncz,
           "equil": args.equil, "prod": args.prod,
           "swap_every": args.swap_every, "seed": args.seed,
           "grad_K_per_A": round(float(grad), 5),
           "profile_K": [round(float(v), 2) for v in prof],
           "fidelity": "pilot/cross-check (single seed, single box)",
           "wall_s": round(time.time() - t0, 1)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in
                      ("x", "T", "kappa_W_mK", "wall_s")}))


if __name__ == "__main__":
    main()
