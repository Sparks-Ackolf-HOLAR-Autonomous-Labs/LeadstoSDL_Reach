#!/bin/bash
# Party 4a production sweep: one array task per composition x_Ge in
# {0, 0.15, 0.2, 0.5, 0.85, 1}; each task builds the 24^3 VCA crystal and
# sweeps T = 300/700/1100 K. Guest partition per the standing directive
# guest/free first, grn061 off-limits.
# Submit:  sbatch --array=0-5 sbatch_bte.sh
#SBATCH --job-name=mt_bte
#SBATCH --partition=notchpeak-guest
#SBATCH --account=owner-guest
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=3:00:00
#SBATCH --requeue
#SBATCH --output=logs/%x_%A_%a.out
set -euo pipefail
XS=(0 0.15 0.2 0.5 0.85 1)
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs
# Restartable by construction: a preempted-and-requeued task reruns its
# composition from scratch (VCAbuilder ~tens of minutes, Tsweep ~minutes).
bash run_bte_point.sh "${XS[$SLURM_ARRAY_TASK_ID]}"
