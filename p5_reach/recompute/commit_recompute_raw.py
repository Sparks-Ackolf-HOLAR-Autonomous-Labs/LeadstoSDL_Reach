#!/usr/bin/env python3
"""Ledger the P5 recompute outputs BEFORE any analysis: one batch_result per unit
with a Merkle root over its out/ files. Refuses if a task is missing, exited
non-zero, or a file would be dropped by .gitignore.
Usage: commit_recompute_raw.py m1c|z1"""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger, leaf_hash, merkle_root  # noqa: E402
unit = sys.argv[1]
N = {"m1c": 51, "z1": 19}[unit]
JOB = {"m1c": "16163392", "z1": "16163393 + 16163394"}[unit]
D = json.load(open(os.path.join(HERE, "recompute_design.json")))
OUT = os.path.join(HERE, unit, "out")
jsons = [f for f in os.listdir(OUT) if f.endswith(".json")]
if len(jsons) != N:
    sys.exit(f"expected {N} outputs, found {len(jsons)}")
for i in range(N):
    if open(os.path.join(OUT, f"task{i}.exit_status")).read().strip() != "0":
        sys.exit(f"task {i} did not exit 0")
files = {}
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    if subprocess.run(["git", "check-ignore", "-q", p]).returncode == 0:
        sys.exit(f"{f} would be dropped by .gitignore")
    files[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
op = f"batch-{D['campaign']}-{unit}"
if any(e["payload"].get("op_id") == op for e in led.entries):
    sys.exit("already committed")
e = led.append("batch_result", {
    "op_id": op, "campaign": D["campaign"], "stage": unit, "rests_on": [133],
    "raw_merkle_root": merkle_root([leaf_hash({"file": k, "sha256": v}) for k, v in sorted(files.items())]),
    "n_files": len(files), "files_sha256": files, "chpc_job": f"{JOB} (notchpeak-guest)",
    "statement": "committed before any analysis of these files"})
assert led.verify_chain()
print("seq", e["seq"])
