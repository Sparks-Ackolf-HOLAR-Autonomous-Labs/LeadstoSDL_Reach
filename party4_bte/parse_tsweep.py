#!/usr/bin/env python3
"""Parse an almaBTE kappa_Tsweep CSV into one JSON per temperature.

Column layout (v1.3.2): T, then (RTA, BTE) pairs for xx, xy, xz, yy, yz,
zz = 13 numeric columns. The header has a known missing-comma quirk on the
last pair, so we parse by numeric position, never by header name. kappa is
the mean of the three diagonal elements (cubic crystal: they agree).
"""
import json
import sys
from pathlib import Path

x = float(sys.argv[1])
grid = int(sys.argv[2])
tsweep = Path(sys.argv[3])
outdir = Path(sys.argv[4])
outdir.mkdir(exist_ok=True)

for line in tsweep.read_text().splitlines():
    line = line.strip().rstrip(",")
    if not line or line[0].isalpha() or line.startswith("Temp"):
        continue
    v = [float(t) for t in line.split(",")]
    T = v[0]
    rta = (v[1] + v[7] + v[11]) / 3.0
    bte = (v[2] + v[8] + v[12]) / 3.0
    xs = f"{x:g}"
    Ts = f"{T:g}"
    tag = f"bte_x{xs}_T{Ts}"
    point = {
        "x": x,
        "T": T,
        "kappa_W_mK": bte,
        "kappa_RTA_W_mK": rta,
        "method": "almaBTE-VCA",
        "party": "BTE-DFT",
        "grid": f"{grid}x{grid}x{grid}",
        "solver": "full iterative BTE (RTA also recorded)",
        "scope_notes": [
            "VCA + mass-disorder: no short-range order, no anharmonic-disorder coupling",
            "perturbative phonons stretched at 1100 K",
            "first-principles parentage (DFT force constants, almaBTE database)",
        ],
        "tag": tag,
    }
    (outdir / f"{tag}.json").write_text(json.dumps(point, indent=1))
    print(f"wrote {tag}: kappa_BTE={bte:.3f} kappa_RTA={rta:.3f} W/mK")
