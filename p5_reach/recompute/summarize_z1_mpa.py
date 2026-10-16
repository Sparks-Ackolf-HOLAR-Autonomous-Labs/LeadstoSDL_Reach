#!/usr/bin/env python3
"""P5 recompute, unit R_Z1 (ledger 133): the committed Z1 analysis
(nano_sigec/si_zone/analyze_zone.py) run unchanged on the MACE-MPA-0 outputs
in z1/out (raw ledgered at 137 before this runs). Only the path is swapped:
a shadow copy of si_zone/ is built in a temporary directory whose chpc/out
points at z1/out; every other input (design, Z2 MD results, small_sic) is the
committed file. Output: zone_mpa_results.json plus claim scores for C8 and C9
of ../reach_prediction.json by their registered refuted_if."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
SZ = os.path.join(MT, "nano_sigec", "si_zone")
OLD = json.load(open(os.path.join(SZ, "zone_results.json")))  # MACE-MP-0, ledger 69-70
tmp = tempfile.mkdtemp()
sh = os.path.join(tmp, "nano_sigec", "si_zone")
os.makedirs(os.path.join(sh, "chpc"))
os.symlink(os.path.join(MT, "nano_sigec", "small_sic"), os.path.join(tmp, "nano_sigec", "small_sic"))
for f in os.listdir(SZ):
    if f not in ("chpc", "zone_results.json"):
        os.symlink(os.path.join(SZ, f), os.path.join(sh, f))
os.symlink(os.path.join(HERE, "z1", "out"), os.path.join(sh, "chpc", "out"))
r = subprocess.run([sys.executable, "-I", os.path.join(sh, "analyze_zone.py")], capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stderr)
NEW = json.load(open(os.path.join(sh, "zone_results.json")))
shutil.rmtree(tmp)

reach = {c["id"]: c for c in json.load(open(os.path.join(HERE, "..", "reach_prediction.json")))["claims"]}
de_new = {str(p["bin"]): p["dE_mean"] for p in NEW["Z1"]["profile"]}
de_old = {str(p["bin"]): p["dE_mean"] for p in OLD["Z1"]["profile"]}
inner = NEW["Z1"]["profile"][0]["dE_mean"]
c8_flip = inner > 0.01
c8 = {"predicted_class": reach["C8_zone_PrZ1"]["predicted_class"],
      "predicted_outcome": reach["C8_zone_PrZ1"]["predicted_outcome"],
      "dE_innermost_old_eV": OLD["Z1"]["profile"][0]["dE_mean"], "dE_innermost_new_eV": inner,
      "refuted": c8_flip,
      "score": ("decision flipped (predicted as may-flip)" if c8_flip else
                "decision held (over-predicted as may-flip)") +
               ("" if -0.25 <= inner <= -0.02 else "; outside the predicted -0.25 to -0.02 eV band: magnitude miss")}
cancel = NEW["decision"]["cancel"]
c9_flip = any(c >= 0.2 for c in cancel)
c9 = {"predicted_class": reach["C9_zone_decision"]["predicted_class"],
      "cancel_old": OLD["decision"]["cancel"], "cancel_new": cancel,
      "branch_old": OLD["decision"]["branch"], "branch_new": NEW["decision"]["branch"],
      "w_eq_1473K_old_A": OLD["Z1"]["w_eq_A_1473K"], "w_eq_1473K_new_A": NEW["Z1"]["w_eq_A_1473K"],
      "refuted": c9_flip,
      "score": "decision flipped: predicted magnitude only, so a miss" if c9_flip else "held as predicted (magnitude only)"}
S = {"source": "P5 recompute R_Z1, MACE-MPA-0 medium (ledger 133, raw 137); comparison = MACE-MP-0 Z1 (ledger 69-70)",
     "gates": {"G1_old": OLD["G1"]["pass"], "G1_new": NEW["G1"]["pass"]},
     "profile_dE_eV": {"MP-0": de_old, "MPA-0": de_new,
                       "shift": {b: de_new[b] - de_old[b] for b in de_new}},
     "PrZ1": {"old": OLD["PrZ1"], "new": NEW["PrZ1"]}, "PrZ4": {"old": OLD["PrZ4"], "new": NEW["PrZ4"]},
     "claim_scores": {"C8": c8, "C9": c9}, "analyze_zone_new": NEW}
json.dump(S, open(os.path.join(HERE, "zone_mpa_results.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in S.items() if k not in ("analyze_zone_new",)}, indent=1))
