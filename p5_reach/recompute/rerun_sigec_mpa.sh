#!/bin/bash
# P5 recompute (ledger 133), downstream of R_M1C: rerun the committed SiGeC analyses unchanged on the
# MACE-MPA-0 summary in a scratch copy (committed results are never overwritten), then compare.
set -e
MT=$(cd "$(dirname "$0")/../.." && pwd); R=$(mktemp -d); P=${PAPER_PY:-$HOME/venvs/mace/bin/python}
export PYTHONDONTWRITEBYTECODE=1
cp -r "$MT"/{nano,nano_sigec,bond_angles,pilot,phase_c} "$R"/
cp "$MT/p5_reach/recompute/m1c_mpa_summary.json" "$R/nano_sigec/m1c/m1c_summary.json"
cd "$R/nano_sigec"
SIGEC_M1_SUMMARY="$R/nano_sigec/m1c/m1c_summary.json" SIGEC_OUT_NAME=sigec_results_m1c.json $P -I analyze_sigec.py >/dev/null
(cd small_sic && $P -I decision_robustness.py >/dev/null)
(cd light_dopants && $P -I analyze_light_dopants.py >/dev/null)
(cd small_sic/r50 && $P -I analyze_r50.py >/dev/null)
O="$MT/p5_reach/recompute/sigec_mpa"; mkdir -p "$O"
cp results/sigec_results_m1c.json "$O/sigec_results_m1c_mpa.json"
cp small_sic/decision_robustness.json "$O/decision_robustness_mpa.json"
cp small_sic/r50/r50_results.json "$O/r50_results_mpa.json"
cp light_dopants/light_dopants_results.json "$O/light_dopants_results_mpa.json"
rm -rf "$R"
$P "$MT/p5_reach/recompute/compare_sigec_mpa.py"
