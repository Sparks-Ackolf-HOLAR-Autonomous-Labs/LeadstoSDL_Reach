#!/usr/bin/env python3
"""Append the P5 GPU recompute registration (R_P4B, R_P3) to the ledger. Commit and push BEFORE submitting."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
files = ["gpu_design.json", "p4b/mp_rnemd_ase.py", "p4b/sbatch_rp4b.sh", "p3/mace_rnemd.py", "p3/points_mpa.json",
         "p3/ids.txt", "p3/sbatch_rp3.sh", "commit_gpu_raw.py", "../../reach_prediction.json"]
sha = {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in files}
d = json.load(open(os.path.join(HERE, "gpu_design.json")))
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
if any(e["payload"].get("design_sha256") == sha["gpu_design.json"] for e in led.entries):
    sys.exit("already registered")
e = led.append("preregistration", {"op_id": "prereg-" + d["campaign"], "campaign": d["campaign"], "paper": d["paper"],
    "parent_campaign": "p5-reach-prediction-mace-version", "rests_on": [130, 133],
    "design_file": "p5_reach/recompute/gpu/gpu_design.json", "design_sha256": sha["gpu_design.json"], "files_sha256": sha,
    "model_checkpoint_sha256": "75428afe3a1d7d8062e19bcaabd5c433623cabf308242ec9fb493e38604fb638",
    "statement": "P5 recompute GPU units R_P4B and R_P3 with MACE-MPA-0 medium: scripts, points and the ledger-130 predictions they grade fixed before submission"})
assert led.verify_chain()
open(os.path.join(HERE, "PREREGISTERED_SHA256"), "w").write(f"{sha['gpu_design.json']}  gpu_design.json  ledger_seq={e['seq']}  entry_hash={e['entry_hash']}\n")
print("seq", e["seq"])
