#!/usr/bin/env python3
"""Ledger the Si-depleted zone outputs (Z1 MACE + Z2 MD) BEFORE analyze_zone.py runs: one
batch_result entry with the Merkle root over every md/results/ file.
Refuses if any of the 19 MACE tasks or 8 MD runs is missing, exited non-zero, or would be
dropped by .gitignore."""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger, leaf_hash, merkle_root  # noqa: E402

D = json.load(open(os.path.join(HERE, "zone_design.json")))
RES = os.path.join(HERE, "md", "results")
OUT = os.path.join(HERE, "chpc", "out")
pts = [l.split() for l in open(os.path.join(HERE, "md", "points.txt")) if l.strip()]
if len(pts) != 8:
    sys.exit("points.txt must list 8 runs")
for tag, _, _, _, _, seed in pts:
    st = os.path.join(RES, f"{tag}_s{seed}.exit_status")
    if not os.path.exists(st) or open(st).read().strip() != "0":
        sys.exit(f"MD {tag}_s{seed} missing or did not exit 0")
for t in range(19):
    st = os.path.join(OUT, f"task{t}.exit_status")
    if not os.path.exists(st) or open(st).read().strip() != "0":
        sys.exit(f"MACE task {t} missing or did not exit 0")
files = {}
for sub, d in (("md/results", RES), ("chpc/out", OUT)):
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if subprocess.run(["git", "check-ignore", "-q", p]).returncode == 0:
            sys.exit(f"{sub}/{f} would be dropped by .gitignore")
        files[f"{sub}/{f}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
leaves = [leaf_hash({"file": k, "sha256": v}) for k, v in sorted(files.items())]
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
op = "batch-" + D["campaign"]
if any(e["payload"].get("op_id") == op for e in led.entries):
    sys.exit("already committed")
e = led.append("batch_result", {
    "op_id": op, "campaign": D["campaign"], "stage": "Z1-MACE+Z2-MD", "raw_merkle_root": merkle_root(leaves),
    "n_files": len(files), "files_sha256": files, "chpc_job": "Z1 15921347 + 15921348, Z2 15921349 (notchpeak-guest)",
    "statement": "committed before analyze_zone.py was run on these files"})
assert led.verify_chain()
print("seq", e["seq"])
