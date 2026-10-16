#!/usr/bin/env python3
"""Record the version-bump analysis and the decision its registered rule selects."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
D = json.load(open(os.path.join(HERE, "design.json")))
A = os.path.join(HERE, "analysis.json"); a = json.load(open(A))
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
camp = D["campaign"]
if any(e["payload"].get("op_id") == f"decision-{camp}" for e in led.entries):
    sys.exit("already recorded")
pre = [e["seq"] for e in led.entries if e["payload"].get("op_id") == f"prereg-{camp}"][0]
bat = [e["seq"] for e in led.entries if e["kind"] == "batch_result" and e["payload"].get("campaign") == camp]
e1 = led.append("analysis", {
    "op_id": f"analysis-{camp}", "campaign": camp, "prereg_seq": pre,
    "results_file": "party5_databases/version_bump/analysis.json",
    "results_sha256": hashlib.sha256(open(A, "rb").read()).hexdigest(),
    "branch": a["branch"], "reach_check_pass": a["reach_check_pass"],
    "predictions": a["predictions"],
    "statement": f"diff and propagation run after the new slice was on the ledger (seq {bat})"})
assert a["branch"] == "no_change" and a["reach_check_pass"]
e2 = led.append("shard_operation", {
    "op_id": f"decision-{camp}", "campaign": camp, "op": "strengthen",
    "target": "DB-STARRY evidence party (645 live points, 37 upstream papers)",
    "decision": f"registered branch no_change (seq {pre}): all three release files changed hash, "
                "the in-scope SiGe slice is byte-identical; blast radius empty; pin moves to data-20261003",
    "evidence": {"analysis_seq": e1["seq"], "batch_seqs": bat}})
assert led.verify_chain()
print("analysis", e1["seq"], "decision", e2["seq"])
