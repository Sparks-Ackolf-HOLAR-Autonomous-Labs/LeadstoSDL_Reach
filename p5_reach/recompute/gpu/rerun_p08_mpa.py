#!/usr/bin/env python3
"""Claim C19 test: rerun detector v2's fault study for entry P08 only (MACE rows
under the Tersoff label), 50 registered trial seeds, with the planted magnitude
recalibrated to MACE-MPA-0 medium: kappa ratio drawn from U(0.70, 0.75)
(R_P4B measured 0.715 and 0.729, in place of U(0.50, 0.60)) and the lattice
ratio from MACE-MPA-0 (Si 5.4674, Ge 5.7192 A, R_M1C M1a, in place of
MACE-MP-0 5.464 / 5.736). Detector, scoring and seeds unchanged. Pr1-Pr7 of
design_v2.json read no P08 trial, so this re-reports the P08 rate only.
Usage: python rerun_p08_mpa.py"""
import json, os, sys, types
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DV = os.path.join(MT, "phase_c", "detector_v2"); PROD = os.path.join(MT, "phase_c", "production")
for p in (os.path.join(PROD, "fault_catalog"), PROD, DV): sys.path.insert(0, p)
f = os.path.join(PROD, "fault_catalog", "inject_faults.py"); src = open(f).read()
a = "r0 = float(rng.uniform(0.50, 0.60))"; assert src.count(a) == 1
IF = types.ModuleType("inject_faults"); IF.__file__ = f; sys.modules["inject_faults"] = IF
exec(compile(src.replace(a, "r0 = float(rng.uniform(0.70, 0.75))"), f + " [P08 recal]", "exec"), IF.__dict__)
import numpy as np, fault_study_v2 as FV
FV.A_MACE = (5.4674, 5.7192)
rows = json.load(open(os.path.join(DV, "rows_v2.json")))
att = FV.Attach(rows); clean = FV.D.detect(rows)
baseline = frozenset(FV._sig(o) for o in clean["ops"])
trials = []
for ts in IF.trial_seeds("P08", 50):
    rows_t, truth = IF.inject(rows, "P08", ts)
    att.apply(rows_t, truth, np.random.default_rng(10_000_000 + ts))
    s = FV.FS.score(FV.D.detect(rows_t), truth, rows_t, baseline); s["trial_seed"] = ts; trials.append(s)
from collections import Counter
summ = {"detected_rate_adj": sum(t["detected_adj"] for t in trials) / 50, "A_adj": dict(Counter(t["outcome_A_adj"] for t in trials)),
        "trials_with_collateral_adj": sum(bool(t["collateral_adj"]) for t in trials),
        "ops_seen": dict(Counter(o for t in trials for o in t["ops_on_affected"]))}
json.dump({"entry": "P08", "recalibration": {"kappa_ratio": [0.70, 0.75], "A_MACE": FV.A_MACE}, "summary": summ, "trials": trials},
          open(os.path.join(HERE, "analysis", "p08_mpa_results.json"), "w"), indent=1, default=str)
print(json.dumps(summ))
