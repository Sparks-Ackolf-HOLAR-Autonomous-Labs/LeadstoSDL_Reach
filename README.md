# Provenance records predict which multi-scale conclusions a foundation-potential release can change in SiGeC semiconductors

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23413463.svg)](https://doi.org/10.5281/zenodo.23413463)

Code, data and figure scripts for the paper "Provenance records predict which multi-scale conclusions a foundation-potential release can change in SiGeC semiconductors" (Modelling and Simulation in Materials Science and Engineering (IOP)). The manuscript itself is not part of this folder.

Licences: code (Python, shell and SLURM scripts) under the MIT License (`LICENSE`); data, result files, figures and text under CC BY 4.0 (`LICENSE-CC-BY-4.0.txt`). Archived third-party datasets keep their own terms and are cited in the paper: the Starrydata slice is CC BY 4.0 (Katsura et al., Sci. Technol. Adv. Mater.: Methods 5, 2506976 (2025), doi:10.1080/27660400.2025.2506976; cite it and the source paper of each curve used), and the Citrine release keeps its published terms.

Every path below is relative to this folder, and every script runs from it. The folder depends on no other folder or repository.

Analysis, figure and checker scripts run on any machine with the Python packages in `requirements.txt`. Acquisition scripts (SLURM job files and run generators) name the cluster paths and simulation binaries (LAMMPS, GPUMD, almaBTE, MACE) used at the time, so re-running a simulation needs those paths edited to the local installation. The recorded outputs of those runs are included, so no simulation has to be repeated to check a result.

Files whose SHA-256 the campaign record stores (designs, pre-registration digests, the scripts and raw outputs they name, and some notes) are kept byte-for-byte as they ran, because any edit would break verification. They keep their original wording, which includes operator decisions with dates, internal step numbers and the run paths of the time. Raw simulation logs are also kept as written.

Terms used in folder names and notes: a *party* is one evidence source of the campaign (for example Tersoff MD, MACE-MP rNEMD, almaBTE first-principles transport or a curated database); a *gate* is the acceptance check a run must pass before its result enters the campaign record; `phase_c/` holds the main campaign and `pilot/` the campaign-record library and the first trial campaign.

## Campaign material

| path | what it holds |
|---|---|
| `p5_reach` | reach prediction, recompute designs, scripts, raw outputs (CPU, GPU, timing), analyses, result summaries and formal statistical tests |
| `nano_sigec/m1c` | original MACE-MP-0 carbon-site relaxations |
| `nano_sigec/si_zone` | original Si-depleted zone check |
| `p3_mace` | original MACE-MP-0 design-check MD and scores |
| `party4_mace` | original MACE-MP-0 rNEMD party |
| `party4_bte` | BTE solves (almaBTE) behind the carbon-free host conductivity |
| `party5_databases` | pinned Starrydata slice of sintered SiGe and the experimental compilation |
| `nano` | effective grain-size calibration on sintered samples |
| `phase_c/ledger_campaign.jsonl` | the campaign record (prediction at entry 130, registrations 133 and 146, decisions 135 to 149) |
| `pilot/src` | campaign-record library |

## Figures

One script draws every figure at its print size into `paper/figure_code/figures/` (PDF used by the paper, PNG for review). Run from this folder with a Python that has numpy, scipy and matplotlib:

    python3 paper/figure_code/make_figures.py

Figures: `fig1_chain`, `fig2_reach`, `fig3_defects`, `fig4_md`, `fig5_cost`, `fig6_margins`.

## Checkers and analyses

| command |
|---|
| `python3 p5_reach/stats/formal_tests.py ` |

## Notes

- `p5_reach/predict_reach.py` made the reach prediction by scanning every script of the full working project, including the other papers' material, for code that reads MACE output. That scan needs the whole project, so the script is kept here as it ran, with its committed output `p5_reach/reach_prediction.json` (hashed at campaign-record entry 130); the figures, tests and recompute analyses in this folder read that output.

`traced_inputs.json` lists every file each command opened when the folder was built; `FILES.sha256` lists the digest of every file in the folder.
