# Release-update drill (2026-10-04)

The executed release update (campaign-record entries 92-95) met a release that left the SiGe
slice byte-identical, so only the `no_change` branch of the registered rule
had run. `drill.py` exercises the other branches on a test release built
from the committed `data-20261003` slice, on a scratch copy under
`/tmp/vbdrill`. The campaign record and committed evidence are not touched;
the operations below were written to a scratch copy of the campaign record.

| Scenario | What the test release does | Branch selected | Reach check | Operations written |
|---|---|---|---|---|
| A, data change | one live curve (sample 21172) scaled by 1.5; one live curve (21933) removed; curve of sample 1344 re-published as 990001 (same values) and as 990002 (kappa x20) | changed_values + removed + added | pass: 0 of 18 moved, added or removed live points lie outside the touched samples | correct 21172 (8 points); quarantine 21933; retain 990001 (9 points pass the bound screen); quarantine 990002 (9 of 9 points fail the bound screen) |
| B, pipeline fault | release unchanged; the ingest copy drops every point above 800 K | no_change | **fail**: 202 live points vanish with no upstream change | deviation (gate failure) instead of any operation |

The x = 0.2 summary medians moved by 1.0% in scenario A, all through the
touched samples. Scenario B shows the reach check doing its job: a silent
change in the pipeline cannot pass as an upstream revision.

Finding: the re-published copy 990001 entered as new evidence. The dedup
guard compares database rows against the literature party by upstream DOI,
not against other curves in the same database, so a curve published twice
under two sample ids would be counted twice. A within-release check on
identical value arrays is needed before the next release update; it is
listed in the release-update design for the next registration.

`apply_branches()` in `drill.py` is the general decision step; the
committed `apply.py` handles only `no_change` and should be replaced by it
at the next registered update.

Rerun: `~/mat_theory_pilot/venv/bin/python drill.py` (about 1 s).
