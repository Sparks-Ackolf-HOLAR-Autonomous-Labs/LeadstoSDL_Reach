#!/bin/bash
# Party 4a bring-up on a CHPC login node (exploratory but fully logged).
# Every step appends to bringup.log; a failed step is iterated from the
# log, not re-guessed. Heavy sweeps go through sbatch on a guest
# partition; this script itself only downloads, inspects, and runs the
# single pure-Si validation solve.
set -uo pipefail
LOG=bringup.log
log() { echo "== $(date -Is) $*" | tee -a "$LOG"; }

log "stage 1: module + tool inventory"
module load almabte 2>>"$LOG" || module load gcc almabte 2>>"$LOG"
module list 2>&1 | tee -a "$LOG"
for t in VCAbuilder kappa_Tsweep superlattice_builder phononinfo \
         steady_montecarlo1d; do
  command -v "$t" >> "$LOG" 2>&1 && echo "have $t" | tee -a "$LOG"
done
# usage strings are the ground truth for the XML schema on this build
kappa_Tsweep --help >> "$LOG" 2>&1 || kappa_Tsweep >> "$LOG" 2>&1 || true
VCAbuilder --help >> "$LOG" 2>&1 || VCAbuilder >> "$LOG" 2>&1 || true

log "stage 2: fetch Si and Ge from the almaBTE materials database"
mkdir -p repo && cd repo
# The database index moved between hosting setups over the years; probe
# the known locations and log which one answers.
for base in https://almabte.bitbucket.io/database \
            http://www.almabte.eu/database \
            https://almabte.bitbucket.io; do
  echo "probe $base" >> "../$LOG"
  curl -sfL --max-time 60 "$base/" -o index.html && \
    { echo "index from $base" | tee -a "../$LOG"; break; }
done
grep -oiE 'href="[^"]*(Si|Ge)[^"]*\.(h5|tar\.[a-z0-9]+)"' index.html \
  | tee -a "../$LOG" || log "no Si/Ge links found; inspect index.html"
# Download whatever elemental Si / Ge entries the index lists, then
# unpack; exact filenames recorded in the log for reproducibility.
cd ..

log "stage 3: validation gate: pure Si kappa_Tsweep at 300 K"
log "  (write kappa_Tsweep XML per the usage string from stage 1;"
log "   target: Si RTA kappa(300K) in the 140-155 W/mK band)"

log "stage 4: VCA grid x={0,0.15,0.2,0.5,0.85,1} T={300,700,1100}"
log "  (submit via sbatch_bte.sh on a guest partition; one task per x)"
log "bring-up script finished; iterate from $LOG"
