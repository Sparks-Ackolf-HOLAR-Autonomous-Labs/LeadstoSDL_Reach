#!/bin/bash
# P5 recompute unit R_P3 (gpu_design.json): the 89 P3 hidden-subset MD runs with
# MACE-MPA-0 medium. Same points, seeds and protocol as p3_mace/chpc (only the
# model string in points_mpa.json changes). Guest GPUs only; checkpointed, requeued.
#   sbatch --array=0-88 sbatch_rp3.sh
#SBATCH --job-name=mt_p5_rp3
#SBATCH --partition=notchpeak-gpu-guest
#SBATCH --account=owner-gpu-guest
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --exclude=notch168,notch294,notch299,notch204,notch215
#SBATCH --output=logs/%x_%A_%a.out
cd "$SLURM_SUBMIT_DIR"; mkdir -p logs out ckpt
ID=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" ids.txt)
[ -s out/$ID.json ] && exit 0
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || exit 3
P=/uufs/chpc.utah.edu/sys/installdir/r8/mace/0.3.16_cu126/.venv/bin/python
$P mace_rnemd.py "$ID" --points points_mpa.json --out out/$ID.json --ckpt-dir ckpt
