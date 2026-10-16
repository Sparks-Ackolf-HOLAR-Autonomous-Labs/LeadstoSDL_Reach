#!/usr/bin/env python3
"""S1: download the new Starrydata release, hash it, extract the SiGe slice
with the unchanged filter, and commit slice + hashes to the ledger before
any comparison. Idempotent per tag."""
import csv, gzip, hashlib, io, json, os, re, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger, leaf_hash, merkle_root  # noqa: E402
D = json.load(open(os.path.join(HERE, "design.json")))
TAG = "data-20261003"
BASE = f"https://github.com/starrydata/starrydata_datasets/releases/download/{TAG}/"
OUT = os.path.join(HERE, "raw_" + TAG)
os.makedirs(OUT, exist_ok=True)
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
op = f"commit-{D['campaign']}-{TAG}"
if any(e["payload"].get("op_id") == op for e in led.entries):
    sys.exit("already committed")
full, blobs = {}, {}
for name in ("all_curves.csv.gz", "all_samples.csv.gz", "all_papers.csv.gz"):
    data = urllib.request.urlopen(BASE + name, timeout=900).read()
    full[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    blobs[name] = gzip.decompress(data).decode()
# filter copied verbatim from open_db/ingest_open_db.fetch_starry
curves = list(csv.DictReader(io.StringIO(blobs["all_curves.csv.gz"])))
keep = [r for r in curves
        if {"Si", "Ge"} <= set(re.findall(r"[A-Z][a-z]?", r["composition"] or ""))
        and "thermal conductivity" in (r["prop_y"] or "").lower()]
sids = {r["sample_id"] for r in keep}
dois = {r["DOI"] for r in keep}
samples = [r for r in csv.DictReader(io.StringIO(blobs["all_samples.csv.gz"]))
           if r["sample_id"] in sids]
papers = [r for r in csv.DictReader(io.StringIO(blobs["all_papers.csv.gz"]))
          if r["DOI"] in dois]
files = {}
for fname, rows in (("starry_sige_kappa_curves.csv", keep),
                    ("starry_sige_samples.csv", samples),
                    ("starry_sige_papers.csv", papers)):
    p = os.path.join(OUT, fname)
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    files[fname] = hashlib.sha256(open(p, "rb").read()).hexdigest()
json.dump({"tag": TAG, "full_release": full, "slice_files": files,
           "n_curves": len(keep), "n_samples": len(samples), "n_papers": len(papers)},
          open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
e = led.append("batch_result", {
    "op_id": op, "campaign": D["campaign"], "stage": TAG,
    "full_release_sha256": {k: v["sha256"] for k, v in full.items()},
    "slice_files_sha256": files,
    "merkle_root": merkle_root([leaf_hash({"file": k, "sha256": v}) for k, v in sorted(files.items())]),
    "statement": "new release slice committed before comparison with the pinned release"})
assert led.verify_chain()
print("seq", e["seq"], len(keep), "curves", json.dumps(full))
