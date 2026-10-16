# Database version bump: Starrydata data-20260928 -> data-20261003

Registered at campaign record seq 92 (`design.json`, `PREREGISTERED_SHA256`) before the new
release was downloaded. New slice committed at seq 93 (`raw_data-20261003/`, with
whole-release hashes in `manifest.json`) before any comparison. Analysis seq 94,
decision seq 95.

Result:
- All three whole-release files changed hash (PrV1 holds): the database is
  regenerated daily and grew between the two tags.
- The in-scope SiGe thermal-conductivity slice is byte-identical (529 curves, same
  samples and papers). Re-running the unchanged ingest and bound screen on it gives
  identical `open_db_points.json`, `INGEST_SUMMARY.json` and `SCREEN_SUMMARY.json`.
- Registered branch `no_change`: an upstream revision event with an empty blast
  radius; the pin of the DB-STARRY party moves to `data-20261003` (`strengthen`).

What it shows: pinning a whole daily-regenerated release would raise a revision
alarm every day; pinning the slice the campaign reads (plus the filter that cuts it)
raises one only when evidence the claims rest on changes.

Rerun: `python3 fetch_new.py` (already committed, refuses), then
`~/mat_theory_pilot/venv/bin/python diff_propagate.py`.

Next registered update: replace `apply.py` by the general decision step in `drill/drill.py` and add a within-release duplicate check on identical value arrays (the drill showed a curve re-published under a new sample id enters as new evidence).
