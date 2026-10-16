#!/bin/bash
# Party 4a: one composition point. VCA build at GRID^3 + kappa_Tsweep over
# T = 300/700/1100 K, RTA + full iterative BTE. Called by sbatch_bte.sh
# with x_Ge as the single argument (x convention: Si_{1-x}Ge_x).
set -euo pipefail
X="$1"
GRID=${GRID:-24}
module load almabte 2>/dev/null
cd "$(dirname "$0")"
WORK="work_x${X}"
mkdir -p "$WORK" results
cd "$WORK"

if [[ "$X" == "0" || "$X" == "1" ]]; then
  NAME=Si; [[ "$X" == "1" ]] && NAME=Ge
  cat > vca.xml <<EOF
<singlecrystal>
  <materials_repository root_directory="../repo"/>
  <compound name="$NAME"/>
  <gridDensity A="$GRID" B="$GRID" C="$GRID"/>
  <target directory="h5"/>
  <overwrite/>
</singlecrystal>
EOF
else
  SI=$(python3 -c "print(round(1-$X, 6))")
  cat > vca.xml <<EOF
<alloy>
  <materials_repository root_directory="../repo"/>
  <compound name="Si" mixfraction="$SI"/>
  <compound name="Ge" mixfraction="$X"/>
  <gridDensity A="$GRID" B="$GRID" C="$GRID"/>
  <target directory="h5"/>
  <overwrite/>
</alloy>
EOF
fi

VCAbuilder vca.xml
H5=$(ls h5/*_${GRID}_${GRID}_${GRID}.h5)
BASE=$(basename "$H5" "_${GRID}_${GRID}_${GRID}.h5")

cat > tsweep.xml <<EOF
<Tsweep>
  <H5repository root_directory="."/>
  <compound directory="h5" base="$BASE" gridA="$GRID" gridB="$GRID" gridC="$GRID"/>
  <sweep type="lin" start="300" stop="1100" points="3"/>
  <fullBTE iterative="true"/>
  <target directory="out" file="AUTO"/>
</Tsweep>
EOF

kappa_Tsweep tsweep.xml
python3 ../parse_tsweep.py "$X" "$GRID" out/*.Tsweep ../results
