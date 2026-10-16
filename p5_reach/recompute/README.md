# P5 recompute, CPU units (registered at campaign-record entries 133, 9 Oct 2026)

Grades the reach prediction of campaign-record entries 130 (`../PREDICTION.md`) for the two
CPU units, with MACE-MPA-0 medium (float64) replacing MACE-MP-0 medium.
Design: `recompute_design.json`. Scripts in `m1c/` and `z1/` are the
committed M1c and Z1 scripts with only the model string changed.

| Unit | CHPC job (notchpeak-guest) | Tasks |
|---|---|---|
| R_M1C | 16163392 | 51 relaxations |
| R_Z1 | 16163393 (reference) then 16163394 (afterok) | 1 + 18 |

Processing: `python3 commit_recompute_raw.py m1c` and `... z1` (raw outputs
hashed onto the campaign record before any analysis), then the
analysis listed in the design and the scoring rule of PREDICTION.md
section 6. Not in this registration: R_P4B and R_P3 (GPU units).
