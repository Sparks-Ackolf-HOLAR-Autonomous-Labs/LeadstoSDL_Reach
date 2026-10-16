#!/usr/bin/env python3
"""Register the database version-bump design on the campaign ledger. Idempotent."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
LEDGER = os.path.join(MT, "phase_c", "ledger_campaign.jsonl")
blob = open(os.path.join(HERE, "design.json"), "rb").read()
sha = hashlib.sha256(blob).hexdigest()
d = json.loads(blob)
led = Ledger(LEDGER)
if any(e["payload"].get("design_sha256") == sha for e in led.entries):
    sys.exit("already registered")
e = led.append("preregistration", {
    "op_id": "prereg-" + d["campaign"], "campaign": d["campaign"], "paper": d["paper"],
    "design_file": "party5_databases/version_bump/design.json", "design_sha256": sha,
    "decision_rule": d["decision_rule"], "predictions": d["predictions"],
    "statement": "procedure, rule and predictions fixed before the new release was downloaded"})
assert led.verify_chain()
open(os.path.join(HERE, "PREREGISTERED_SHA256"), "w").write(
    f"{sha}  design.json  ledger_seq={e['seq']}  entry_hash={e['entry_hash']}\n")
print("seq", e["seq"], sha)
