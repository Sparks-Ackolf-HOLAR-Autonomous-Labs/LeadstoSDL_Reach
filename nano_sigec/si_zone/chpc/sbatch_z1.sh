#!/bin/bash
# Si-depleted zone check, stage Z1 (../zone_design.json). Guest partition only
# (grn061 off-limits by operator directive; DGX reserved).
# Task 0 = reference relaxation; tasks 1-18 need out/ref_relaxed.extxyz:
#   jid=$(sbatch --parsable --array=0 sbatch_z1.sh)
#   sbatch --dependency=afterok:$jid --array=1-18 sbatch_z1.sh
#SBATCH --job-name=mt_zone_z1
#SBATCH --partition=notchpeak-guest
#SBATCH --account=owner-guest
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=10:00:00
#SBATCH --requeue
#SBATCH --output=logs/%x_%A_%a.out
cd "$SLURM_SUBMIT_DIR"; mkdir -p logs out ckpt
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
P=/uufs/chpc.utah.edu/sys/installdir/r8/mace/0.3.16_cu126/.venv/bin/python
T=$SLURM_ARRAY_TASK_ID
$P mace_zone.py "$T" && echo 0 > out/task$T.exit_status || echo $? > out/task$T.exit_status
