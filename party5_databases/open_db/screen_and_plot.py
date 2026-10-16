#!/usr/bin/env python3
"""Cross-party bound screen (standing rule since the MACE unit slip) and
the headline figure for the open-database experimental party.

Bound: a real Si(1-x)Ge(x) sample cannot conduct phonons much better than
the perfect-crystal first-principles (BTE-DFT, VCA) value at the same x, T.
Total kappa adds an electronic part (<~1-2 W/mK in heavily doped TE SiGe),
so the flag threshold is kappa > 1.3 * BTE + 1.5 W/mK. BTE is interpolated
in x on its grid (x = 0, 0.15, 0.2, 0.5, 0.7, 0.85, 1) and in T (300, 700,
1100 K); points outside the BTE T grid are not screened.
"""
import glob, json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
bte = {}
for f in glob.glob(str(PROJ / "party4_bte/results/*.json")):
    d = json.loads(Path(f).read_text())
    for r in (d if isinstance(d, list) else [d]):
        bte[(r["x"], r["T"])] = r["kappa_W_mK"]
xs = sorted({k[0] for k in bte}); Ts = [300.0, 700.0, 1100.0]
grid = np.array([[bte.get((x, T), np.nan) for T in Ts] for x in xs])

def bte_at(x, T):
    if not (300 <= T <= 1100):
        return None
    lg = np.log(grid)
    col = [np.interp(x, xs, lg[:, j]) for j in range(3)]
    return float(np.exp(np.interp(T, Ts, col)))

pts = json.loads((HERE / "open_db_points.json").read_text())
live = [p for p in pts if not p["dedup_suspect"]]
nflag = 0
for p in pts:
    b = bte_at(p["x_ge"], p["T_K"])
    p["bte_bound"] = None if b is None else round(b, 3)
    p["bound_flag"] = b is not None and p["kappa_W_mK"] > 1.3 * b + 1.5
    nflag += p["bound_flag"] and not p["dedup_suspect"]
(HERE / "open_db_points.json").write_text(json.dumps(pts, indent=1))
flagged = [(p["upstream"]["doi"], p["upstream"]["composition"], p["system"], p["T_K"], p["kappa_W_mK"], p["bte_bound"])
           for p in live if p["bound_flag"]]

# x ~ 0.2 slice: the RTG composition, where the open data are densest
sel = [p for p in live if 0.18 <= p["x_ge"] <= 0.22]
fig, ax = plt.subplots(figsize=(7, 4.6))
styles = {"nanostructured": ("#d9480f", "o", "sintered / nanostructured"),
          "bulk": ("#1864ab", "s", "bulk (melt / single crystal)"),
          "other": ("#868e96", ".", "form not recorded"),
          "nanowire": ("#2b8a3e", "^", "nanowire"), "film": ("#862e9c", "v", "film")}
for sys_, (c, m, lab) in styles.items():
    q = [p for p in sel if p["system"] == sys_]
    if q:
        ax.scatter([p["T_K"] for p in q], [p["kappa_W_mK"] for p in q], c=c, marker=m, s=18, alpha=.7,
                   label=f"Starrydata: {lab} (n={len(q)})")
Tl = np.linspace(300, 1100, 50)
ax.plot(Tl, [bte_at(0.2, t) for t in Tl], "k-", lw=2, label="BTE-DFT perfect crystal, x=0.2")
cit = json.loads((HERE.parent / "party5_points.json").read_text())
cq = [c for c in cit if 0.18 <= c["x_ge"] <= 0.22 and not c["dedup_suspect"]]
ax.scatter([c["T_K"] for c in cq], [c["kappa_W_mK"] for c in cq], facecolors="none", edgecolors="k", s=40,
           label=f"Citrine (party 5, n={len(cq)})")
ax.set_xlabel("T (K)"); ax.set_ylabel("kappa (W/mK, total unless noted)")
ax.set_title("Si0.8Ge0.2: open experimental data vs first-principles bulk")
ax.legend(fontsize=7, loc="upper right"); ax.set_ylim(0, 12)
fig.tight_layout(); fig.savefig(HERE / "fig_open_db_x02.png", dpi=150)

def stats(q):
    k = np.array([p["kappa_W_mK"] for p in q]); return (len(q), round(float(np.median(k)), 2)) if len(k) else (0, None)
out = {"bound_flagged_live": nflag, "flagged": flagged,
       "x02_300K_median_by_system": {s: stats([p for p in sel if p["system"] == s and p["T_K"] == 300]) for s in styles},
       "x02_900K_median_by_system": {s: stats([p for p in sel if p["system"] == s and p["T_K"] == 900]) for s in styles},
       "bte_x02": {T: round(bte_at(0.2, T), 2) for T in (300.0, 900.0)}}
(HERE / "SCREEN_SUMMARY.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
