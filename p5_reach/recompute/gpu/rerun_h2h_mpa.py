#!/usr/bin/env python3
"""R_P4B analysis step 2 (gpu_design.json 'analysis'): rerun the P1 head-to-head
(phase_c/head_to_head/head_to_head.py, ledger 63-67) with the two MACE rows
swapped for the MACE-MPA-0 outputs of R_P4B. The script's code is executed
unchanged except for three data/IO substitutions, each asserted to match once:
  E1 MACE rows  -> R_P4B outputs (corrected units, as the fixed script writes them)
  E0 MACE rows  -> R_P4B outputs x 1/units.fs^2 (103.6427), so E0 keeps the
                   planted-as-first-ingested unit-slip fault of ledger 1
  output file   -> analysis/h2h_mpa_results.json
Run with --no-pysr (C12 concerns the pipeline row and the MF-GP rows only).
Usage: ~/mat_theory_pilot/venv/bin/python rerun_h2h_mpa.py --no-pysr"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
H2H = os.path.join(MT, "phase_c", "head_to_head", "head_to_head.py")
SLIP = 103.6427
NEW = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(HERE, "p4b", "out", "mpa_*.json")))]
assert len(NEW) == 2
src = open(H2H).read()
subs = [
    ('RAW_MACE = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(MT, "party4_mace", "raw", "mace_*.json")))]',
     'RAW_MACE = [dict(m, kappa_W_mK=m["kappa_W_mK"] * %r) for m in __NEW__]' % SLIP),
    ('mace = [row(q, "mace") for q in kg if q.get("corpusId") == "MACE-MD"]',
     'mace = [{"x": m["x"], "T": m["T"], "kappa": m["kappa_W_mK"], "party": "mace", "system": "bulk"} for m in __NEW__]'),
    ('os.path.join(HERE, "h2h_results.json")', 'os.path.join(__OUTDIR__, "h2h_mpa_results.json")'),
]
for a, b in subs:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
os.makedirs(os.path.join(HERE, "analysis"), exist_ok=True)
G = {"__file__": H2H, "__name__": "__main__", "__NEW__": NEW, "__OUTDIR__": os.path.join(HERE, "analysis")}
exec(compile(src, H2H + " [R_P4B swap]", "exec"), G)
