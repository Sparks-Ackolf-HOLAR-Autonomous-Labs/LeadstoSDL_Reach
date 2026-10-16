#!/usr/bin/env python3
"""Hash R_P4B or R_P3 outputs onto the ledger before any analysis. Usage: commit_gpu_raw.py p4b|p3"""
import glob, hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
u = sys.argv[1]; assert u in ("p4b", "p3")
fs = sorted(glob.glob(os.path.join(HERE, u, "out", "*.json"))); assert fs
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
pre = [e["seq"] for e in led.entries if e["payload"].get("campaign") == "p5-mace-version-recompute-gpu-2026-10-10" and e["kind"] == "preregistration"]
e = led.append("batch_result", {"campaign": "p5-mace-version-recompute-gpu-2026-10-10", "unit": {"p4b": "R_P4B", "p3": "R_P3"}[u],
    "prereg_seq": pre, "files_sha256": {os.path.relpath(f, MT): hashlib.sha256(open(f, "rb").read()).hexdigest() for f in fs},
    "statement": f"{len(fs)} outputs committed before analysis"})
assert led.verify_chain(); print("seq", e["seq"], len(fs))
