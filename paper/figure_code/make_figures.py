"""Figures of the P5 draft (Modelling Simul. Mater. Sci. Eng., IOP).

Every data figure is drawn from committed result files of the project; no
number is typed in by hand except the panel layout. Run from any directory:

    python3 make_figures.py

Figures are created at their true print size (IOP text width 153 mm), so a
7 pt tick label is 7 pt on the page; draft.tex includes them at natural size.

Files read (paths relative to the project root):
  p5_reach/reach_prediction.json                 Fig. 2 (reach by link type)
  nano_sigec/m1c/m1c_summary.json                Fig. 3 a, b (MACE-MP-0)
  p5_reach/recompute/m1c_mpa_summary.json        Fig. 3 a, b (MACE-MPA-0)
  p5_reach/recompute/zone_mpa_results.json       Fig. 3 c (both models)
  p3_mace/raw/out/*.json                         Fig. 4 a, Fig. 5 b (old runs)
  p5_reach/recompute/gpu/p3/out/*.json           Fig. 4 a, Fig. 5 b (new runs)
  p3_mace/results/p3_mace_results.json           Fig. 4 b (old design scores)
  p5_reach/recompute/gpu/analysis/p3_mpa_results.json  Fig. 4 b (new scores)
  p5_reach/recompute/gpu/analysis/gpu_mpa_summary.json Fig. 4 a (median ratio)
  nano_sigec/m1c/out, nano_sigec/si_zone/chpc/out, party4_mace/raw,
  p5_reach/recompute/{m1c,z1}/out, p5_reach/recompute/gpu/p4b/out
                                                 Fig. 5 a (recorded wall times)
  p5_reach/reach_prediction.json, p3_mace/results  Fig. 6 (margins)
Fig. 1 is a diagram of the model chain (no data).
"""
import glob
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figures"
PROJECT = HERE.parents[1]  # project root

FULL = 6.02  # IOP text width 153 mm, inches
COL = 2.95   # half width, inches

INK = "#333333"
GREY = "#8C8C8C"
OLD = "#0072B2"   # MACE-MP-0 (Okabe-Ito blue)
NEW = "#D55E00"   # MACE-MPA-0 (Okabe-Ito vermillion)
OTHER = "#009E73"
LIGHT = "#EBEBEB"


def apply_style():
    plt.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 600,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.grid": True,
        "grid.color": "#DDDDDD",
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "lines.linewidth": 1.2,
        "legend.frameon": False,
        "figure.constrained_layout.use": True,
        "pdf.fonttype": 42,
    })


def save(fig, name):
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGDIR / f"{name}.pdf", facecolor="white", metadata={"CreationDate": None})
    fig.savefig(FIGDIR / f"{name}.png", dpi=300, facecolor="white")
    w, h = fig.get_size_inches()
    plt.close(fig)
    print(f"wrote figures/{name}.pdf ({w:.2f} x {h:.2f} in)")


def load(rel):
    return json.load(open(PROJECT / rel))


def panel(ax, letter):
    ax.text(-0.02, 1.02, f"({letter})", transform=ax.transAxes, ha="right",
            va="bottom", fontsize=8, fontweight="bold")


# ---------------------------------------------------------------- Fig. 1
def fig_chain():
    fig = plt.figure(figsize=(FULL, 2.35))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")

    def box(x, y, w, h, title, body, edge, dy=8.4):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc="white", ec=edge, lw=1.1))
        ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=7.5,
                fontweight="bold")
        ax.text(x + w / 2, y + h - dy, body, ha="center", va="top", fontsize=6.5,
                linespacing=1.25)

    def arrow(x0, y0, x1, y1, c=INK):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0))

    top, h = 17.5, 20.5
    box(1, top, 17, h, "Foundation\npotential",
        "MACE-MP-0\n(medium, small)\nreplaced by\nMACE-MPA-0\n(medium)", NEW)
    box(22, top, 20, h, "Atomistic\ncalculations",
        "relaxed defect energies\n(where carbon goes,\nGe around SiC)\nmolecular-dynamics\nconductivity", NEW)
    box(46, top, 20, h, "Scattering model\nand surrogates",
        "phonon modes plus\npoint-defect and SiC-\nparticle scattering;\nfitted surrogates and\nmulti-fidelity models", NEW)
    box(70, top, 29, h, "Decisions and\nconclusions",
        "recipe pick (Ge, C, SiC size)\nGe saving at equal\nconductivity; batch-design\nverdicts; composition pick\nat 1100 K; cost plans", NEW)
    for x0, x1 in [(18.8, 21.2), (42.8, 45.2), (66.8, 69.2)]:
        arrow(x0, top + h / 2, x1, top + h / 2, NEW)

    box(22, 1.2, 44, 11.2, "Sources outside the potential",
        "Tersoff molecular dynamics; DFT phonon Boltzmann\ntransport; published and compiled measurements", OTHER, dy=5.0)
    arrow(56, 13.3, 56, 16.6, OTHER)
    arrow(62, 13.3, 76, 16.6, OTHER)
    ax.text(83.5, 7.5, "Record entries, analysis code\nand manuscript lines record\nwhich step read which output",
            ha="center", va="center", fontsize=6.5, color=GREY, style="italic")
    save(fig, "fig1_chain")


# ---------------------------------------------------------------- Fig. 2
def fig_reach():
    d = load("p5_reach/reach_prediction.json")
    tiers = d["reach_by_tier"]
    order = ["T0_explicit", "T1_plus_prose_citations", "T2_plus_file_paths", "T3_plus_campaign_names"]
    labels = ["explicit fields\nand operation names", "+ citations in\nfree text",
              "+ shared analysis\ncode (file paths)", "+ shared campaign\nnames"]
    n = [tiers[k]["n_entries"] for k in order]
    total = d["ledger_read"]["n_entries"]
    fig, ax = plt.subplots(figsize=(COL, 1.9))
    y = np.arange(len(n))[::-1]
    prev = 0
    for yi, ni in zip(y, n):
        ax.barh(yi, prev, color=GREY, height=0.6)
        ax.barh(yi, ni - prev, left=prev, color=NEW, height=0.6)
        ax.text(ni + 1.5, yi, f"{ni}", va="center", fontsize=7)
        prev = ni
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlim(0, total)
    ax.set_xlabel(f"record entries reached (of {total})")
    ax.grid(axis="y", visible=False)
    save(fig, "fig2_reach")


# ---------------------------------------------------------------- Fig. 3
def fig_defects():
    old = load("nano_sigec/m1c/m1c_summary.json")["per_x"]
    new = load("p5_reach/recompute/m1c_mpa_summary.json")["per_x"]
    zone = load("p5_reach/recompute/zone_mpa_results.json")["profile_dE_eV"]
    fig, axs = plt.subplots(1, 3, figsize=(FULL, 2.2))
    xs = ["0", "0.2", "0.5"]
    xv = np.array([0, 0.2, 0.5])
    # (a) energy gained by carbon leaving the lattice as SiC
    ax = axs[0]
    for summ, c, lab, off in [(old, OLD, "MACE-MP-0", -0.012), (new, NEW, "MACE-MPA-0", 0.012)]:
        vals = [summ[k]["dE_prec_eV"] for k in xs]
        mean = np.array([np.mean(v) for v in vals])
        lo = mean - np.array([min(v) for v in vals])
        hi = np.array([max(v) for v in vals]) - mean
        ax.errorbar(xv + off, mean, yerr=[lo, hi], fmt="o-", color=c, ms=3.5, capsize=2, label=lab)
    ax.axhline(-0.5, color=GREY, ls="--", lw=0.8)
    ax.text(0.5, -0.43, "registered threshold", ha="right", va="bottom", fontsize=6.5, color=GREY)
    ax.set_xlabel("Ge fraction $x$ of the host")
    ax.set_ylabel("$\\Delta E_\\mathrm{prec}$ (eV per C)")
    ax.set_ylim(-2.7, 0.0)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.62))
    panel(ax, "a")
    # (b) carbon beside Ge rather than Si
    ax = axs[1]
    xs2 = ["0.2", "0.5"]
    for summ, c, lab, off in [(old, OLD, "MACE-MP-0", -0.012), (new, NEW, "MACE-MPA-0", 0.012)]:
        vals = [[s["dE_site"] for s in summ[k]["site_pref"]] for k in xs2]
        mean = np.array([np.mean(v) for v in vals])
        lo = mean - np.array([min(v) for v in vals])
        hi = np.array([max(v) for v in vals]) - mean
        ax.errorbar(np.array([0.2, 0.5]) + off, mean, yerr=[lo, hi], fmt="o", color=c, ms=3.5,
                    capsize=2, label=lab)
    ax.axhline(0, color=GREY, ls="--", lw=0.8)
    ax.set_xlim(0.1, 0.6)
    ax.set_xticks([0.2, 0.5])
    ax.set_xlabel("Ge fraction $x$ of the host")
    ax.set_ylabel("$\\Delta E_\\mathrm{site}$ (eV)")
    ax.set_ylim(-0.05, 0.5)
    panel(ax, "b")
    # (c) Ge segregation energy around a SiC particle
    ax = axs[2]
    for key, c, lab in [("MP-0", OLD, "MACE-MP-0"), ("MPA-0", NEW, "MACE-MPA-0")]:
        dd = sorted((float(k), v) for k, v in zone[key].items())
        ax.plot([a for a, _ in dd], [b for _, b in dd], "o-", color=c, ms=3.5, label=lab)
    ax.plot([6.0, 7.0], [0.01, 0.01], color=GREY, ls="--", lw=0.9)
    ax.axhline(0, color=INK, lw=0.5)
    ax.text(6.0, 0.022, "flip threshold,\nfirst shell", ha="left", va="bottom", fontsize=6.5,
            color=GREY)
    ax.set_xlabel("distance to SiC centre (Å)")
    ax.set_ylabel("Ge segregation energy (eV)")
    ax.set_ylim(-0.19, 0.08)
    panel(ax, "c")
    save(fig, "fig3_defects")


# ---------------------------------------------------------------- Fig. 4
def _p3_runs():
    rows = []
    for f in sorted(glob.glob(str(PROJECT / "p3_mace/raw/out/*.json"))):
        name = Path(f).name
        g = PROJECT / "p5_reach/recompute/gpu/p3/out" / name
        if not g.exists():
            continue
        a, b = json.load(open(f)), json.load(open(g))
        card = lambda e: re.search(r"\((.*)\)", e).group(1).replace("NVIDIA ", "")  # noqa: E731
        rows.append(dict(T=a["T_K"], k_old=a["kappa_W_mK"], k_new=b["kappa_W_mK"],
                         h_old=a["wall_s_this_attempt"] / 3600, h_new=b["wall_s_this_attempt"] / 3600,
                         card_old=card(a["engine"]), card_new=card(b["engine"])))
    return rows


def fig_md():
    rows = _p3_runs()
    summ = load("p5_reach/recompute/gpu/analysis/gpu_mpa_summary.json")
    med = summ["p3_level_shift_mpa_over_mp0"]["median"]
    so = load("p3_mace/results/p3_mace_results.json")["scores"]
    sn = load("p5_reach/recompute/gpu/analysis/p3_mpa_results.json")["scores"]
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 2.45), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    markers = {300: ("o", "300 K"), 700: ("s", "700 K"), 1100: ("^", "1100 K")}
    for T, (m, lab) in markers.items():
        r = [x for x in rows if x["T"] == T]
        ax.scatter([x["k_old"] for x in r], [x["k_new"] for x in r], marker=m, s=12,
                   facecolor="none", edgecolor=INK, lw=0.7, label=lab)
    lim = np.array([0.25, 2.2])
    ax.plot(lim, lim, color=GREY, lw=0.8, ls="--", label="equal")
    ax.plot(lim, med * lim, color=NEW, lw=1.0, label=f"median ratio {med:.2f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    from matplotlib.ticker import FixedLocator, NullLocator, FormatStrFormatter
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(FixedLocator([0.3, 0.5, 1.0, 2.0]))
        axis.set_minor_locator(NullLocator())
        axis.set_major_formatter(FormatStrFormatter("%g"))
    ax.set_xlabel("$\\kappa$, MACE-MP-0 small (W m$^{-1}$ K$^{-1}$)")
    ax.set_ylabel("$\\kappa$, MACE-MPA-0 medium (W m$^{-1}$ K$^{-1}$)")
    ax.legend(loc="lower right", fontsize=6.5, handlelength=1.4)
    panel(ax, "a")
    ax = axs[1]
    designs = [("CA1", "covering, 15 runs", "RND15"), ("OFAT", "one factor\nat a time, 12", "RND12"),
               ("CA2", "double covering, 30", None), ("RND_pool", "random, 30", None)]
    y = np.arange(len(designs))[::-1]
    for yi, (k, lab, ref) in zip(y, designs):
        ax.plot([so[k]["log_rmse"], sn[k]["log_rmse"]], [yi, yi], color=GREY, lw=0.8, zorder=1)
        ax.scatter([so[k]["log_rmse"]], [yi], color=OLD, s=18, zorder=2,
                   label="MACE-MP-0" if yi == y[0] else None)
        ax.scatter([sn[k]["log_rmse"]], [yi], color=NEW, s=18, zorder=2,
                   label="MACE-MPA-0" if yi == y[0] else None)
        if ref:
            for s, c, dy in [(so, OLD, 0.22), (sn, NEW, -0.22)]:
                q = s[ref]["log_rmse_q25_q75"]
                ax.plot(q, [yi + dy, yi + dy], color=c, lw=2.2, alpha=0.35, solid_capstyle="butt")
                ax.plot([s[ref]["log_rmse"]], [yi + dy], "|", color=c, ms=6)
    ax.set_yticks(y)
    ax.set_yticklabels([d[1] for d in designs], fontsize=6.5)
    ax.set_xlabel("log RMSE on 16 hidden recipes")
    ax.set_xlim(0.05, 0.2)
    ax.set_ylim(-0.6, len(designs) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=6.5)
    ax.text(0.198, y[0] + 0.42, "bars: random batches of\nequal size (median, IQR)", ha="right",
            va="bottom", fontsize=6, color=GREY)
    panel(ax, "b")
    save(fig, "fig4_md")


# ---------------------------------------------------------------- Fig. 5
def _wall(pat, key="wall_s"):
    tot = 0.0
    for f in glob.glob(str(PROJECT / pat)):
        tot += json.load(open(f))[key]
    return tot / 3600


def fig_cost():
    units = [
        ("defect energies\n51 relaxations", "nano_sigec/m1c/out/*.json", "p5_reach/recompute/m1c/out/*.json", "wall_s", "CPU"),
        ("Ge around SiC\n19 relaxations", "nano_sigec/si_zone/chpc/out/*.json", "p5_reach/recompute/z1/out/*.json", "wall_s", "CPU"),
        ("conductivity offset\n2 MD runs", "party4_mace/raw/*.json", "p5_reach/recompute/gpu/p4b/out/*.json", "wall_s", "GPU"),
        ("SiGeC design space\n89 MD runs", "p3_mace/raw/out/*.json", "p5_reach/recompute/gpu/p3/out/*.json", "wall_s_this_attempt", "GPU"),
    ]
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 2.4), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axs[0]
    y = np.arange(len(units))[::-1]
    for yi, (lab, po, pn, key, kind) in zip(y, units):
        o, n = _wall(po, key), _wall(pn, key)
        ax.barh(yi + 0.18, o, height=0.34, color=OLD, label="old model (recorded)" if yi == y[0] else None)
        ax.barh(yi - 0.18, n, height=0.34, color=NEW, label="new model (measured)" if yi == y[0] else None)
        unit = "CPU-task-h" if kind == "CPU" else "GPU-h"
        ax.text(n * 1.15, yi - 0.18, f"{n:.1f} {unit}", va="center", fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlim(0.5, 5000)
    ax.set_yticks(y)
    ax.set_yticklabels([u[0] for u in units], fontsize=6.5)
    ax.set_xlabel("compute per unit (h)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper right", fontsize=6.5)
    panel(ax, "a")
    ax = axs[1]
    rows = _p3_runs()
    cards = sorted({r["card_new"] for r in rows} | {r["card_old"] for r in rows},
                   key=lambda c: -np.median([r["h_new"] for r in rows if r["card_new"] == c] or [0]))
    rng = np.random.default_rng(0)
    for i, c in enumerate(cards):
        ho = [r["h_old"] for r in rows if r["card_old"] == c]
        hn = [r["h_new"] for r in rows if r["card_new"] == c]
        if ho:
            ax.scatter(i - 0.17 + rng.uniform(-0.07, 0.07, len(ho)), ho, s=6, color=OLD, alpha=0.8, lw=0)
        if hn:
            ax.scatter(i + 0.17 + rng.uniform(-0.07, 0.07, len(hn)), hn, s=6, color=NEW, alpha=0.8, lw=0)
    ax.set_xticks(range(len(cards)))
    ax.set_xticklabels([c.replace("GeForce ", "").replace(" 40GB Active", "").replace("Tesla ", "")
                        for c in cards], rotation=35, ha="right", fontsize=6.5)
    ax.set_ylabel("GPU-h per MD run (1152 atoms)")
    ax.set_ylim(0, 9)
    ax.grid(axis="x", visible=False)
    panel(ax, "b")
    save(fig, "fig5_cost")


# ---------------------------------------------------------------- Fig. 6
# Registered thresholds (p5_reach/PREDICTION.md): precipitation -0.5 eV,
# first-shell flip +0.01 eV; sign thresholds (0) for the Ge trend and the
# site preference; the covering verdict holds while covering is worse than
# the random median. Scales: plausible version shift (reach_prediction.json)
# for energies, replicate-seed difference (p3_mace_results.json) for MD.
def fig_margins():
    rp = load("p5_reach/reach_prediction.json")
    d = rp["plausible_version_shift_eV"]
    old = load("nano_sigec/m1c/m1c_summary.json")["per_x"]
    new = load("p5_reach/recompute/m1c_mpa_summary.json")["per_x"]
    zone = load("p5_reach/recompute/zone_mpa_results.json")["profile_dE_eV"]
    o3 = load("p3_mace/results/p3_mace_results.json")
    n3 = load("p5_reach/recompute/gpu/analysis/p3_mpa_results.json")
    noise = max(o3["noise_floor_abs_log_diff"])

    def prec(s):
        return min(-0.5 - s[x]["dE_prec_mean_eV"] for x in ("0", "0.2", "0.5"))

    def trend(s):
        return -(s["0.5"]["dE_prec_mean_eV"] - s["0"]["dE_prec_mean_eV"])

    def site(s):
        return min(s[x]["dE_site_mean_eV"] for x in ("0.2", "0.5"))

    def cov(r):
        return r["scores"]["CA1"]["log_rmse"] - r["scores"]["RND15"]["log_rmse"]

    rows = [("carbon leaves the lattice as SiC", prec(old), prec(new), d, "eV"),
            ("precipitation more favourable with Ge", trend(old), trend(new), d, "eV"),
            ("carbon prefers Si-rich shells", site(old), site(new), d, "eV"),
            ("SiC attracts Ge in the first shell", 0.01 - zone["MP-0"]["6.5"], 0.01 - zone["MPA-0"]["6.5"], d, "eV"),
            ("covering no better than random", cov(o3), cov(n3), noise, "in ln\u03ba")]
    fig, ax = plt.subplots(figsize=(FULL, 2.15))
    ax.axvspan(-1, 1, color=LIGHT, zorder=0)
    ax.axvline(0, color=INK, lw=0.9)
    for i, (lab, a, b, sc, u) in enumerate(rows):
        ax.annotate("", xy=(b / sc, i), xytext=(a / sc, i),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9, shrinkA=3, shrinkB=3))
        ax.plot(a / sc, i, "o", color=OLD, ms=5, zorder=3)
        ax.plot(b / sc, i, "o", color=NEW, ms=5, zorder=3)
        ax.text(1.01, i, f"{a:+.2g} \u2192 {b:+.2g} {u}", fontsize=6.3,
                va="center", ha="left", color=INK, transform=ax.get_yaxis_transform())
    ax.plot([], [], "o", color=OLD, label="MACE-MP-0")
    ax.plot([], [], "o", color=NEW, label="MACE-MPA-0")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim(-0.8, 5.6)
    ax.set_xlabel("margin to the deciding threshold, in units of the plausible shift")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=6.5)
    save(fig, "fig6_margins")


if __name__ == "__main__":
    apply_style()
    fig_chain()
    fig_reach()
    fig_defects()
    fig_md()
    fig_cost()
    fig_margins()
