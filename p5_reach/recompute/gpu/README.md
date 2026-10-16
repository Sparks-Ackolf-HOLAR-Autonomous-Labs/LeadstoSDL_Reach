# P5 recompute, GPU units (registered at campaign-record entries 146, 10 Oct 2026)

R_P4B (two party-4b MD points) and R_P3 (all 89 P3 hidden-subset MD runs)
repeated with MACE-MPA-0 medium in place of MACE-MP-0 small. Design:
`gpu_design.json`; scripts byte-identical to the originals, only the model
string changes.

| Unit | CHPC job (notchpeak-gpu-guest) | Tasks | Expected cost |
|---|---|---|---|
| R_P4B | 16172247 | 2 (x = 0.5, 0.15) | about 23 h per point on an A6000-class card |
| R_P3 | 16172248 | 89 | about 3 to 4 h per run |

Collect: `./fetch_gpu.sh`, then `python3 commit_gpu_raw.py p4b` and
`... p3` (raw hashed before analysis), then the analysis in the design and
the scoring rule of `../../PREDICTION.md` section 6.

Collected 2026-10-11 (campaign-record entries 147-149): all 91 runs done, all ten claims C10-C19 hold. See `RESULTS_GPU.md`.
