# P5 GPU units: model-change timing (timing only, no science output)

Old model MACE-MP-0 small (as used in party 4b and P3) against new model
MACE-MPA-0 medium, float32, plain torch (cuEquivariance not available in the
CHPC mace/0.3.16 module), same card per job.

| Job | Card | Box | Old ms/step | New ms/step | Ratio |
|---|---|---|---|---|---|
| 16163796 | RTX 2080 Ti (11 GB) | P3, 1152 atoms | 107 | 225 | 2.1 |
| 16163796 | RTX 2080 Ti (11 GB) | party 4b, 3072 atoms | 429 | out of memory | n/a |
| 16165498 | RTX A6000 (48 GB) | P3, 1152 atoms | 77.4-77.8 | 182.3-183.8 | 2.36 |
| 16165498 | RTX A6000 (48 GB) | party 4b, 3072 atoms | 279 | 549 | 1.97 |

The kappa values in `out/` come from 400-step runs and are not physical.

Cost of the two GPU units with the new model (recorded old cost times the
measured ratio; the old costs were recorded on other cards, so these are
estimates, not measurements):

| Unit | Recorded old cost | New-model estimate | Card needed |
|---|---|---|---|
| R_P4B (2 points, 3072 atoms) | 8.1 GPU-h (DGX GB10) | about 16 GPU-h | at least 24 GB (fails on 11 GB) |
| R_P3 (89 runs, 1152 atoms) | 150 GPU-h (mixed guest cards) | about 350 GPU-h | any; 2080 Ti runs it at 2.1x |

Neither unit is registered or submitted. The A6000 job was chosen from five
parallel submissions (A40, A6000, L40, A100, 3090); the other four were
cancelled before starting.
