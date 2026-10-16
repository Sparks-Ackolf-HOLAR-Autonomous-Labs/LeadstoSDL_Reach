#!/bin/bash
# P5 recompute unit R_P4B (gpu_design.json): the two party-4b MD points with
# MACE-MPA-0 medium. Same box (4x4x24, 3072 atoms), seed 101, 20k + 130k steps,
# swap every 50 as party4_mace (only --model changes). Needs >= 24 GB (out of
# memory on 11 GB). The script has no checkpoint: a preemption restarts the point.
#   sbatch --array=0-1 sbatch_rp4b.sh
#SBATCH --job-name=mt_p5_rp4b
#SBATCH --partition=notchpeak-gpu-guest
#SBATCH --account=owner-gpu-guest
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --constraint="a6000|a40|l40|a100|3090"
#SBATCH --time=36:00:00
#SBATCH --requeue
#SBATCH --exclude=notch168,notch294,notch299,notch204,notch215,notch103,notch329
#SBATCH --output=logs/%x_%A_%a.out
cd "$SLURM_SUBMIT_DIR"; mkdir -p logs out
X=$( [ "$SLURM_ARRAY_TASK_ID" = 0 ] && echo 0.5 || echo 0.15 )
O=out/mpa_x${X}_T300_z24.json
[ -s $O ] && exit 0
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || exit 3
P=/uufs/chpc.utah.edu/sys/installdir/r8/mace/0.3.16_cu126/.venv/bin/python
$P mp_rnemd_ase.py --x $X --T 300 --ncx 4 --ncy 4 --ncz 24 --equil 20000 --prod 130000 --swap-every 50 --seed 101 --model medium-mpa-0 --out $O
