#!/bin/bash
# Si-depleted zone check, stage Z2 (../zone_design.json). Guest partition only:
# grn061 is off-limits by operator directive, the DGX is reserved.
# Submit ONLY after zone_design.json is on the ledger and pushed:
#   sbatch --array=0-7 sbatch_zone.sh
#SBATCH --job-name=mt_zone
#SBATCH --partition=notchpeak-guest
#SBATCH --account=owner-guest
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --mem=48G
#SBATCH --time=10:00:00
#SBATCH --requeue
#SBATCH --output=logs/%x_%A_%a.out
set -euo pipefail
module load openmpi/4.1.6 lammps
cd "$SLURM_SUBMIT_DIR"; mkdir -p results logs
read -r TAG R W SHELL SIC SEED <<< "$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" points.txt)"
OUT="results/${TAG}_s${SEED}"
mpirun -np "$SLURM_NTASKS" lmp -in in.sic_zone -log "${OUT}.log" -screen none \
  -var ncxy 16 -var ncz 48 -var R "$R" -var w "$W" -var shell "$SHELL" -var sic "$SIC" \
  -var seed "$SEED" -var pot SiCGe_GeC.tersoff -var out "$OUT"
python3 analyze_mp.py "${OUT}.log" "${OUT}.profile" "${OUT}.json"
echo 0 > "${OUT}.exit_status"
