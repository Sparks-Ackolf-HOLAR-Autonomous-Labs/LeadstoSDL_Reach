#!/usr/bin/env python3
"""Append the Si-depleted zone check pre-registration to the campaign ledger.
Idempotent on the design hash. Commit and push BEFORE submitting the job."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402

files = ["zone_design.json", "chpc/mace_zone.py", "chpc/sbatch_z1.sh", "md/in.sic_zone", "md/SiCGe_GeC.tersoff", "md/points.txt", "md/sbatch_zone.sh", "md/analyze_mp.py"]
sha = {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in files}
d = json.load(open(os.path.join(HERE, "zone_design.json")))
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
if any(e["payload"].get("design_sha256") == sha["zone_design.json"] for e in led.entries):
    sys.exit("already registered")
e = led.append("preregistration", {
    "op_id": "prereg-" + d["campaign"], "campaign": d["campaign"], "paper": d["paper"],
    "parent_campaign": d["parent_campaign"], "design_file": "nano_sigec/si_zone/zone_design.json",
    "design_sha256": sha["zone_design.json"], "files_sha256": sha,
    "gates": sorted(d["gates"]), "predictions": sorted(d["predictions"]),
    "statement": "structures, potential file, gates, predictions and decision rule fixed before any production run; only a MACE build check and two single-point force timings (1728 atoms, DGX CPU, 4 threads) were run"})
assert led.verify_chain()
open(os.path.join(HERE, "PREREGISTERED_SHA256"), "w").write(
    f"{sha['zone_design.json']}  zone_design.json  ledger_seq={e['seq']}  entry_hash={e['entry_hash']}\n")
print("seq", e["seq"], sha["zone_design.json"])
