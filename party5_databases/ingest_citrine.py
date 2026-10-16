#!/usr/bin/env python3
"""Party 5 ingestion: curated-database evidence under the derived-evidence
entry rules (06_evidence_party_roadmap.md).

Source: the Citrine experimental thermal-conductivity dataset as
distributed by matminer (`citrine_thermal_conductivity`), 872 compounds.
The release is pinned by figshare file id AND sha256; a hash mismatch is
a hard failure, because a silent version bump must instead be processed
as an upstream revision event on the ledger (P2's versioning story).

Entry rules applied here:
- party type derived/aggregated; party id DB-CITRINE
- upstream identity: this flattened release carries no per-row DOI, so
  upstream identity is (dataset id, release sha256, row index, formula);
  rows therefore enter with the aggregator as the citable upstream and a
  weaker-provenance flag, exactly the caveat the roadmap recorded
- independence weight from the upstream method (experiment), not from
  the database
- numeric dedup against the literature party (no shared DOI to key on):
  a row within (dx<=0.02, dT<=25 K, dkappa<=5%) of an existing
  literature point is kept in this file but flagged `dedup_suspect` and
  excluded from the hypergraph, so aggregated evidence can never
  double-count a paper the literature party already read

Scope filter: binary diamond-lattice Si(1-x)Ge(x), plus dilutely doped
Si-Ge (total dopant fraction < 2 at%, the RTG-alloy lineage), plus pure
Si/Ge. Compounds that merely contain Si and Ge (e.g. Mg2(Si,Ge) Zintl
phases) are out of scope for the kappa(x, T) campaign.

Run:  python3 ingest_citrine.py            (uses cached download if present)
Out:  party5_points.json (all rows + flags), and the hypergraph builder
      pilot/kg/extract_kg.py picks up the unflagged rows as party 5.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

DATASET_ID = "citrine_thermal_conductivity"
FIGSHARE_URL = "https://ndownloader.figshare.com/files/13314470"
PINNED_SHA256 = ("8490997195d6ec912705a5b2322726e53a72c26143"
                 "a7e63fe0f962ccc6232b2c")
CACHE = HERE / "citrine_thermal_conductivity.json.gz"

DOPANTS = {"P", "B", "As", "Sb", "Ga", "Al"}


def fetch() -> list[dict]:
    if not CACHE.exists():
        urllib.request.urlretrieve(FIGSHARE_URL, CACHE)
    raw = CACHE.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != PINNED_SHA256:
        raise SystemExit(
            f"HASH MISMATCH for {DATASET_ID}: got {sha}. Treat as an "
            "upstream revision event (ledger), do not silently ingest.")
    d = json.loads(gzip.decompress(raw))
    return [dict(zip(d["columns"], r)) for r in d["data"]]


def parse_formula(f: str):
    """Return (x_ge, dopant_frac, dopants) for in-scope formulas, else None."""
    f = f.strip()
    if f in ("Si", "Ge"):
        return (0.0 if f == "Si" else 1.0), 0.0, []
    toks = re.findall(r"([A-Z][a-z]?)([0-9.]*)", f)
    if not toks or "".join(e + n for e, n in toks) != f:
        return None
    amounts = {}
    for el, n in toks:
        amounts[el] = amounts.get(el, 0.0) + (float(n) if n else 1.0)
    si, ge = amounts.pop("Si", 0.0), amounts.pop("Ge", 0.0)
    if si <= 0 or ge <= 0:
        return None
    if set(amounts) - DOPANTS:
        return None                      # Mg2Si0.6Ge0.4 etc: out of scope
    total = si + ge + sum(amounts.values())
    dop = sum(amounts.values()) / total
    if dop >= 0.02:
        return None
    return ge / (si + ge), dop, sorted(amounts)


def parse_T(row):
    c = str(row.get("k_condition", "")).strip()
    try:
        t = float(c)
        return (t, False) if str(row.get("k_condition_units",
                                         "")).strip() == "K" else (t, False)
    except ValueError:
        pass
    if "room" in c.lower() or "standard" in c.lower():
        return 300.0, True
    return None, False


def main():
    rows = fetch()
    lit = json.loads(
        (HERE.parent / "pilot" / "kg" / "extracted_points.json").read_text())
    lit = [p for p in lit if not str(p.get("corpusId", "")).startswith(
        ("DGX-", "CHPC-", "DB-", "MACE-", "BTE-"))]

    points, skipped = [], 0
    for i, row in enumerate(rows):
        parsed = parse_formula(str(row.get("formula", "")))
        if parsed is None:
            skipped += 1
            continue
        x_ge, dop_frac, dopants = parsed
        T, T_assumed = parse_T(row)
        if T is None or row.get("k_expt") in (None, ""):
            continue
        kappa = float(row["k_expt"])
        dup = any(
            p.get("x_ge") is not None and abs(float(p["x_ge"]) - x_ge) <= 0.02
            and p.get("T_K") is not None and abs(float(p["T_K"]) - T) <= 25
            and abs(float(p["kappa_W_mK"]) - kappa)
            <= 0.05 * max(float(p["kappa_W_mK"]), 1e-9)
            for p in lit)
        points.append({
            "x_ge": round(x_ge, 4), "T_K": T, "kappa_W_mK": kappa,
            "system": "bulk", "method": "experiment",
            "corpusId": "DB-CITRINE",
            "title": ("Derived party: Citrine experimental thermal "
                      "conductivity (matminer citrine_thermal_conductivity, "
                      "figshare 13314470, 2018-10 release)"),
            "snippet_hash": f"row{i}_{row['formula']}",
            "query_file": "party5",
            "party_type": "derived/aggregated",
            "upstream": {"dataset": DATASET_ID,
                         "figshare_file": 13314470,
                         "sha256": PINNED_SHA256,
                         "row_index": i,
                         "formula": row["formula"],
                         "per_row_doi": None},
            "dopants": dopants, "dopant_frac": round(dop_frac, 5),
            "T_assumed_room": T_assumed,
            "dedup_suspect": dup,
        })
    out = HERE / "party5_points.json"
    out.write_text(json.dumps(points, indent=2))
    n_dup = sum(p["dedup_suspect"] for p in points)
    print(f"in-scope points={len(points)} (dedup_suspect={n_dup}, "
          f"doped={sum(1 for p in points if p['dopants'])}) "
          f"out-of-scope rows skipped={skipped} -> {out}")


if __name__ == "__main__":
    main()
