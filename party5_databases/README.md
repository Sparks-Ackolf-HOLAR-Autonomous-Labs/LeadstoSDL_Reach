# Party 5: curated-database evidence (derived/aggregated)

The fifth evidence party, executed 2026-09-27. Design rationale and entry rules: `../06_evidence_party_roadmap.md`.

## What is ingested

`ingest_citrine.py` ingests the Citrine experimental thermal-conductivity
dataset (matminer `citrine_thermal_conductivity`, 872 compounds), pinned to
the 2018-10 figshare release (file 13314470) by sha256. The cached release
file is committed next to the script so the ingestion is reproducible
offline and the pin is testable. In-scope rows (binary Si1-xGex, dilutely
doped Si-Ge below 2 at%, pure Si/Ge; Zintl and clathrate Si/Ge compounds
excluded): **17 datapoints**, including Si0.8Ge0.2 at 300-1000 K, the
P- and B-doped RTG-lineage alloys, one x=0.5 point, and pure Si at
298-1273 K. Pure-Si high-temperature rows are the only experimental
evidence in the campaign reaching the x0T3/x0T4 regimes, which is exactly
where the GPUMD endpoint campaign will land its simulation points.

## Entry rules, as implemented

| Rule (roadmap) | Implementation |
|---|---|
| party type `derived/aggregated` | `party_type` field on every row; party id `DB-CITRINE` |
| upstream identity per row | this release carries no per-row DOI, so upstream identity is (dataset id, release sha256, row index, raw formula), and the weaker-provenance caveat is recorded on the row (`per_row_doi: null`) |
| version pinned in the campaign record | sha256 verified on every run; mismatch is a hard failure with instructions to process it as an upstream revision event (P2's versioning story), never a silent re-ingest |
| dedup against the literature party | numeric proximity check (dx <= 0.02, dT <= 25 K, dkappa <= 5%); suspects stay in `party5_points.json` flagged `dedup_suspect` and are excluded from the hypergraph. First run caught exactly one: pure Si 150 W/mK at 298 K vs the literature party's 148 |
| independence weight from the upstream method | rows enter as `method: experiment`; the hypergraph groups them under the experiment method vertex, not under a database pseudo-method |

## Files

- `ingest_citrine.py` - the ingester (pin check, scope filter, dedup)
- `citrine_thermal_conductivity.json.gz` - the pinned release, cached
- `party5_points.json` - all in-scope rows with flags; the hypergraph
  builder (`../pilot/kg/extract_kg.py`) picks up unflagged rows

## Not ingested yet, deliberately

- **starrydata2**: multi-GB dumps, needs its own scoped extraction; same
  entry rules apply when it comes.
- **Materials Project**: carries no kappa; its role is P3's ternary
  stability screen (formation energies), which needs an MP API key.
- **AFLOW-AGL**: Debye-model kappa estimates; would enter as model-class
  evidence, not experimental. Low priority until a fit wants it.
