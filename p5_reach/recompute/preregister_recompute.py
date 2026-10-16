#!/usr/bin/env python3
"""Append the P5 CPU recompute registration to the campaign ledger.
Idempotent on the design hash. Commit and push BEFORE submitting."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402

files = ["recompute_design.json", "m1c/mace_relax_m1c.py", "m1c/sbatch_m1c.sh",
         "z1/mace_zone.py", "z1/sbatch_z1.sh", "../reach_prediction.json"]
sha = {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in files}
d = json.load(open(os.path.join(HERE, "recompute_design.json")))
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
if any(e["payload"].get("design_sha256") == sha["recompute_design.json"] for e in led.entries):
    sys.exit("already registered")
e = led.append("preregistration", {
    "op_id": "prereg-" + d["campaign"], "campaign": d["campaign"], "paper": d["paper"],
    "parent_campaign": "p5-reach-prediction-mace-version", "rests_on": [130],
    "design_file": "p5_reach/recompute/recompute_design.json",
    "design_sha256": sha["recompute_design.json"], "files_sha256": sha,
    "model_checkpoint_sha256": "75428afe3a1d7d8062e19bcaabd5c433623cabf308242ec9fb493e38604fb638",
    "statement": "P5 recompute units R_M1C and R_Z1 with MACE-MPA-0 medium: scripts, model checkpoint hash and the ledger-130 predictions they grade fixed before submission"})
assert led.verify_chain()
open(os.path.join(HERE, "PREREGISTERED_SHA256"), "w").write(
    f"{sha['recompute_design.json']}  recompute_design.json  ledger_seq={e['seq']}  entry_hash={e['entry_hash']}\n")
print("seq", e["seq"])
