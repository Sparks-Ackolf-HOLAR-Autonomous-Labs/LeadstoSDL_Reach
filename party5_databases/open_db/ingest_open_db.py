#!/usr/bin/env python3
"""Party 5b/5c ingestion: open experimental databases that replace the
paywalled-PDF plan (2026-09-29: no group archive, no instrument budget,
so the experimental party must come from open data).

Sources (both derived/aggregated, entry rules of 06_evidence_party_roadmap.md):

  DB-STARRY  Starrydata2 (NIMS; digitized published curves, per-sample DOI),
             GitHub release starrydata/starrydata_datasets "latest". The
             release is REGENERATED DAILY, so the exact snapshot we used is
             pinned by the manifest sha256s below and the SiGe slice is
             committed verbatim under raw/ (the upstream file will not stay
             available). A hash mismatch on refetch is an upstream revision
             event for the ledger, never a silent re-ingest.
  DB-UCSB    UCSB/MRL experimental thermoelectrics (Gaultois et al. 2013),
             matminer `ucsb_thermoelectrics`, figshare file 28333845,
             per-row DOI. Also used to resolve the upstream DOI of
             Citrine rows, which carry none (exact numeric match).

Entry rules applied:
  - scope: diamond-lattice Si(1-x)Ge(x), dilute dopants (<2 at%, from
    {P,B,As,Sb,Ga,Al}), no composites / second phases (FeSi2, WSi2, oxides)
  - Starrydata: DataType == "Reference" (a curve re-plotted from another
    paper) is excluded as a duplicate by construction
  - ambiguous compositions ("SiGe" with no numbers) excluded, counted
  - curves are sampled only inside their measured T range (no
    extrapolation) at 300, 400, ..., 1300 K
  - kappa_type recorded: total vs lattice. Heavily doped TE samples report
    TOTAL kappa, which includes an electronic part our MD/BTE parties do
    not compute; the flag travels with every point
  - dedup, in order: (1) upstream DOI already read by the literature
    party -> dedup_suspect; (2) UCSB rows that numerically duplicate a
    Starrydata curve of the same DOI -> dedup_suspect; flagged rows are
    kept in the output but excluded from the hypergraph

Run:  python3 ingest_open_db.py [--fetch]   (default: committed raw/ slice)
Out:  open_db_points.json, INGEST_SUMMARY.json
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
PROJ = HERE.parents[1]

# Immutable dated release tag holding exactly the pinned snapshot (its
# manifest.json carries the same three sha256s; verified 2026-09-29 by
# papers/bib_audit/verify_data_sources.py). "latest" is regenerated daily
# and would fail the pin on any later refetch.
STARRY_BASE = ("https://github.com/starrydata/starrydata_datasets/"
               "releases/download/data-20260928/")
STARRY_PINNED = {  # manifest generated_at 2026-09-28T23:13:38Z, db_snapshot 2026-09-29 02:00 JST
    "all_curves.csv.gz":
        "8e971d266bbdc073471f8220d3576e28cad1c60b7d392667c37911675026f1d7",
    "all_samples.csv.gz":
        "d3999e22b19dc2c5e5d71acbb6185e62cbfef84d274def9726fb43a162087091",
    "all_papers.csv.gz":
        "3e4f99386c01f56093e30133e8766598cc7abb00b13098b5a179de31888dbbd8",
}
UCSB_URL = "https://ndownloader.figshare.com/files/28333845"
UCSB_SHA = "7d0c9c74fd52995b876bd251a7732b5498314702441fa463197fb492be68ecc0"

DOPANTS = {"P", "B", "As", "Sb", "Ga", "Al"}
T_GRID = list(range(300, 1301, 100))


def parse_formula(f: str):
    """(x_ge, dopant_frac, dopants) for in-scope formulas, else a reason str."""
    f = f.strip()
    toks = re.findall(r"([A-Z][a-z]?)((?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)?)", f)
    if not toks or "".join(e + n for e, n in toks) != f:
        return "composite_or_unparsable"
    if all(n == "" for _, n in toks) and len(toks) > 1:
        return "ambiguous_no_stoichiometry"
    amounts: dict[str, float] = {}
    for el, n in toks:
        amounts[el] = amounts.get(el, 0.0) + (float(n) if n else 1.0)
    si, ge = amounts.pop("Si", 0.0), amounts.pop("Ge", 0.0)
    if si <= 0 or ge <= 0:
        return "not_binary_sige"
    if set(amounts) - DOPANTS:
        return "non_dopant_element"
    total = si + ge + sum(amounts.values())
    dop = sum(amounts.values()) / total
    if dop >= 0.02:
        return "dopant_ge_2at%"
    return ge / (si + ge), dop, sorted(amounts)


def sample_class(info: dict) -> str:
    def cat(k):
        v = info.get(k, {})
        return (v.get("category", "") if isinstance(v, dict) else str(v)) or ""
    form, fab = cat("Form"), cat("FabricationProcess")
    if form == "Film" or fab == "FilmGrowth":
        return "film"
    if form == "Wire" or fab == "VaporGrowth":
        return "nanowire"
    if form == "SingleCrystal" or fab == "MeltGrowth":
        return "bulk"                       # single crystal
    if fab in ("PressureSintering", "Sintering"):
        return "nanostructured"            # sintered powder compacts (grain size not in metadata)
    if fab == "Melting":
        return "bulk"
    return "other"


def fetch_starry():
    """Download the full release, check pins, write the SiGe slice to raw/."""
    RAW.mkdir(exist_ok=True)
    blobs = {}
    for name, sha in STARRY_PINNED.items():
        data = urllib.request.urlopen(STARRY_BASE + name, timeout=600).read()
        got = hashlib.sha256(data).hexdigest()
        if got != sha:
            raise SystemExit(f"HASH MISMATCH {name}: {got}. Upstream revision "
                             "event: ledger it, do not silently ingest.")
        blobs[name] = gzip.decompress(data).decode()
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
    for fname, rows in (("starry_sige_kappa_curves.csv", keep),
                        ("starry_sige_samples.csv", samples),
                        ("starry_sige_papers.csv", papers)):
        with open(RAW / fname, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    ucsb = urllib.request.urlopen(UCSB_URL, timeout=300).read()
    if hashlib.sha256(ucsb).hexdigest() != UCSB_SHA:
        raise SystemExit("HASH MISMATCH ucsb_thermoelectrics")
    (RAW / "ucsb_thermoelectrics.json.gz").write_bytes(ucsb)


def load_csv(name):
    with open(RAW / name, newline="") as fh:
        return list(csv.DictReader(fh))


def interp(xs, ys, t):
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if x0 <= t <= x1 and x1 > x0:
            return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
    return None


def main():
    if "--fetch" in sys.argv or not (RAW / "starry_sige_kappa_curves.csv").exists():
        fetch_starry()

    lit = json.loads((PROJ / "pilot" / "kg" / "extracted_points.json").read_text())
    lit_titles = {str(p.get("title", "")).lower().strip() for p in lit
                  if not str(p.get("corpusId", "")).startswith(
                      ("DGX-", "CHPC-", "DB-", "MACE-", "BTE-"))}
    # Literature party carries Semantic Scholar corpusIds and titles, not DOIs;
    # the DOI-level key is resolved through the Starrydata paper titles.
    papers = {r["DOI"].lower(): r for r in load_csv("starry_sige_papers.csv")}
    samples = {r["sample_id"]: r for r in load_csv("starry_sige_samples.csv")}

    reasons: dict[str, int] = {}
    points = []
    curve_keys = set()
    for r in load_csv("starry_sige_kappa_curves.csv"):
        parsed = parse_formula(r["composition"] or "")
        if isinstance(parsed, str):
            reasons[parsed] = reasons.get(parsed, 0) + 1
            continue
        x_ge, dop, dopants = parsed
        s = samples.get(r["sample_id"], {})
        info = json.loads(s["sample_info"]) if s.get("sample_info") else {}
        dtype = (info.get("DataType") or {}).get("category", "") if isinstance(info.get("DataType"), dict) else ""
        if dtype == "Reference":
            reasons["replotted_reference_curve"] = reasons.get("replotted_reference_curve", 0) + 1
            continue
        if r["prop_x"] != "Temperature" or r["unit_x"] != "K" or not r["unit_y"].startswith("W*m^(-1)*K^(-1)"):
            reasons["axis_not_T_or_units"] = reasons.get("axis_not_T_or_units", 0) + 1
            continue
        if "lattice" in r["prop_y"].lower():
            ktype = "lattice"
        elif "electron" in r["prop_y"].lower():
            reasons["electronic_kappa_curve"] = reasons.get("electronic_kappa_curve", 0) + 1
            continue
        else:
            ktype = "total"
        xs = json.loads(r["x"]); ys = json.loads(r["y"])
        pairs = sorted(zip(xs, ys))
        xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]
        doi = (r["DOI"] or "").lower()
        ptitle = (papers.get(doi, {}).get("title") or "").strip('"')
        in_lit = ptitle.lower().strip() in lit_titles
        cls = sample_class(info)
        for T in T_GRID:
            k = interp(xs, ys, T)
            if k is None:
                continue
            curve_keys.add((doi, round(x_ge, 3), T))
            points.append({
                "x_ge": round(x_ge, 4), "T_K": float(T), "kappa_W_mK": round(k, 4),
                "system": cls, "method": "experiment",
                "corpusId": "DB-STARRY",
                "title": "Derived party: Starrydata2 digitized curves (release 2026-09-28, sha-pinned)",
                "snippet_hash": f"sid{r['sample_id']}_fig{r['figure_id']}_T{T}",
                "query_file": "party5b",
                "party_type": "derived/aggregated",
                "kappa_type": ktype,
                "upstream": {"dataset": "starrydata2", "doi": doi,
                             "paper_title": ptitle, "sample_id": r["sample_id"],
                             "figure": r["figure_name"], "composition": r["composition"],
                             "curves_sha256": STARRY_PINNED["all_curves.csv.gz"]},
                "measurement": ((info.get("ThermalMeasurement") or {}).get("category", "")
                                if isinstance(info.get("ThermalMeasurement"), dict) else ""),
                "dopants": dopants, "dopant_frac": round(dop, 5),
                "dedup_suspect": in_lit,
                "dedup_reason": "upstream paper already in literature party" if in_lit else None,
            })

    # Upstream identity: Starrydata DOIs resolved to Semantic Scholar
    # corpusIds through Asta (get_paper_batch, asta_doi_resolution.json);
    # a corpusId the literature party already read is a duplicate.
    res_f = HERE / "asta_doi_resolution.json"
    if res_f.exists():
        res = json.loads(res_f.read_text())
        doi2cid = {d: str(r["corpusId"]) for d, r in zip(res["dois"], res["asta"])
                   if isinstance(r, dict) and r.get("corpusId")}
        lit_cids = {str(p.get("corpusId")) for p in lit}
        for p in points:
            cid = doi2cid.get(p["upstream"]["doi"])
            p["upstream"]["s2_corpusId"] = cid
            if cid and cid in lit_cids:
                p["dedup_suspect"] = True
                p["dedup_reason"] = "upstream corpusId already in literature party"

    # UCSB rows (per-row DOI); dedup against Starrydata curves of the same DOI
    u = json.loads(gzip.decompress((RAW / "ucsb_thermoelectrics.json.gz").read_bytes()))
    cols = u["columns"]
    ucsb_rows = [dict(zip(cols, row)) for row in u["data"]]
    for i, row in enumerate(ucsb_rows):
        parsed = parse_formula(str(row["composition"]))
        if isinstance(parsed, str) or row.get("kappa [W/mK]") in (None,) or row["kappa [W/mK]"] != row["kappa [W/mK]"]:
            continue
        x_ge, dop, dopants = parsed
        src = str(row["src"])
        doi = src.split("doi.org/")[-1].lower() if "doi.org/" in src else None
        dup = doi is not None and (doi, round(x_ge, 3), float(row["T [K]"])) in curve_keys
        cls = "nanostructured" if "nano" in str(row["synthesis"]).lower() or row["crystallinity"] == "Nanoparticles" else "bulk"
        points.append({
            "x_ge": round(x_ge, 4), "T_K": float(row["T [K]"]),
            "kappa_W_mK": float(row["kappa [W/mK]"]), "system": cls,
            "method": "experiment", "corpusId": "DB-UCSB",
            "title": "Derived party: UCSB/MRL thermoelectrics (matminer ucsb_thermoelectrics, figshare 28333845)",
            "snippet_hash": f"row{i}_{row['composition']}_T{row['T [K]']}",
            "query_file": "party5c", "party_type": "derived/aggregated",
            "kappa_type": "total",
            "upstream": {"dataset": "ucsb_thermoelectrics", "doi": doi,
                         "row_index": i, "composition": row["composition"],
                         "synthesis": row["synthesis"], "sha256": UCSB_SHA},
            "dopants": dopants, "dopant_frac": round(dop, 5),
            "dedup_suspect": dup,
            "dedup_reason": "same DOI/x/T as a Starrydata curve" if dup else None,
        })

    # Resolve Citrine rows' missing upstream DOI through exact UCSB matches
    cit = json.loads((HERE.parent / "party5_points.json").read_text())
    resolved = []
    for c in cit:
        for p in points:
            if (p["corpusId"] == "DB-UCSB" and abs(p["kappa_W_mK"] - c["kappa_W_mK"]) < 1e-4
                    and abs(p["T_K"] - c["T_K"]) < 1 and abs(p["x_ge"] - c["x_ge"]) < 0.01):
                resolved.append({"citrine_row": c["snippet_hash"], "doi": p["upstream"]["doi"],
                                 "ucsb_row": p["snippet_hash"]})
                if not p["dedup_suspect"]:
                    p["dedup_suspect"] = True
                    p["dedup_reason"] = "identical to a Citrine row already in party 5"
    (HERE / "open_db_points.json").write_text(json.dumps(points, indent=1))
    live = [p for p in points if not p["dedup_suspect"]]
    summ = {
        "starry_curves_in_slice": len(load_csv("starry_sige_kappa_curves.csv")),
        "excluded_curves_by_reason": reasons,
        "points_total": len(points), "points_live": len(live),
        "live_by_party": {k: sum(p["corpusId"] == k for p in live) for k in ("DB-STARRY", "DB-UCSB")},
        "live_by_system": {s: sum(p["system"] == s for p in live) for s in sorted({p["system"] for p in live})},
        "live_by_kappa_type": {t: sum(p["kappa_type"] == t for p in live) for t in ("total", "lattice")},
        "live_upstream_papers": len({p["upstream"]["doi"] for p in live}),
        "x_ge_values": sorted({p["x_ge"] for p in live}),
        "dedup_flagged": len(points) - len(live),
        "citrine_rows_doi_resolved_via_ucsb": resolved,
    }
    (HERE / "INGEST_SUMMARY.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps({k: v for k, v in summ.items() if k != "citrine_rows_doi_resolved_via_ucsb"}, indent=1))
    print("citrine rows resolved:", len(resolved))


if __name__ == "__main__":
    main()
