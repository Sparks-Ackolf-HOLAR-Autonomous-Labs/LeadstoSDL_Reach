#!/bin/bash
# P5 GPU units: timing only (no science output). Same guest GPU times the old
# model (MACE-MP-0 small) and the new one (MACE-MPA-0 medium) on the P3 box
# (3x3x16, 300 MD steps) and the party-4b box (4x4x24 = 3072 atoms, 300 steps),
# so the cost ratio is measured on one card. Guest partition only.
# Rerun of 16163796 on a 48 GB A40: MACE-MPA-0 medium ran out of memory on the
# 11 GB RTX 2080 Ti for the 3072-atom party-4b box.
#SBATCH --job-name=mt_p5_gputime_a40
#SBATCH --partition=notchpeak-gpu-guest
#SBATCH --account=owner-gpu-guest
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --gres=gpu:a40:1
#SBATCH --time=00:40:00
#SBATCH --exclude=notch168,notch294,notch299,notch204,notch215
#SBATCH --output=logs/%x_%j.out
cd "$SLURM_SUBMIT_DIR"; mkdir -p logs out
nvidia-smi --query-gpu=name --format=csv,noheader || exit 3
P=/uufs/chpc.utah.edu/sys/installdir/r8/mace/0.3.16_cu126/.venv/bin/python
for m in small mpa; do
  for id in bench_disp bench_clu; do
    $P mace_rnemd.py $id --points bench_points_$m.json --out out/a40_p3_${m}_$id.json --ckpt-dir ckpt_$m --bench 300
  done
done
for m in small medium-mpa-0; do
  ( /usr/bin/time -f "WALL %e s" $P mp_rnemd_ase.py --x 0.5 --T 300 --equil 300 --prod 100 --model $m --out out/a40_p4b_$m.json ) 2>&1 | grep -E "equil done|WALL|cueq|Error" | sed "s/^/p4b $m: /"
done
