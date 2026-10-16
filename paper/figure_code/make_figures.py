"""Figures of the P5 draft (Modelling Simul. Mater. Sci. Eng., IOP).

Every data figure is drawn from committed result files of the project; no
number is typed in by hand except the panel layout. Run from any directory:

    python3 make_figures.py

Figures are created at their true print size (IOP text width 153 mm), so a
7 pt tick label is 7 pt on the page; draft.tex and esi.tex include them at
natural size.

Main text
  fig1_chain    diagram of the model chain and the campaign record (no data)
  fig2_defects  nano_sigec/m1c/m1c_summary.json (MACE-MP-0),
                p5_reach/recompute/m1c_mpa_summary.json (MACE-MPA-0),
                p5_reach/recompute/zone_mpa_results.json (both; far-site
                scatter computed from the 9.5-13.5 A bins)
  fig3_md       p3_mace/raw/out/*.json and p5_reach/recompute/gpu/p3/out/*.json
                (paired conductivities), p3_mace/results/p3_mace_results.json
                and p5_reach/recompute/gpu/analysis/p3_mpa_results.json (design
                scores, repeat-seed differences),
                p5_reach/stats/stats_results.json (median ratio, bootstrap CI)
  fig4_margins  p5_reach/reach_prediction.json, the defect-energy and zone
                files above, the two design-score files above
  fig5_cost     recorded and measured wall times (nano_sigec/m1c/out,
                nano_sigec/si_zone/chpc/out, party4_mace/raw, p3_mace/raw/out,
                p5_reach/recompute/{m1c,z1}/out, p5_reach/recompute/gpu/{p4b,p3}/out),
                registered estimate p5_reach/recompute/gpu/gpu_design.json
ESI
  figS1_reach   p5_reach/reach_prediction.json (record entries per link type)
  figS2_cards   per-run GPU-hours by card from the two design-space out/ folders
"""
import glob
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402
from matplotlib.ticker import FixedLocator, FormatStrFormatter, NullLocator  # noqa: E402

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
# temperature (sequential purple, kept apart from the two release colours)
TCOL = {300: "#B4A7D6", 700: "#7B5BA8", 1100: "#3F0F5F"}
MINUS = "−"


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
        "axes.unicode_minus": True,
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


def sig2(v):
    """Two significant figures, explicit sign, true minus sign."""
    if v == 0:
        return "0"
    d = max(1 - int(np.floor(np.log10(abs(v)))), 0)
    return f"{v:+.{d}f}".replace("-", MINUS)


# ---------------------------------------------------------------- Fig. 1
def fig_chain():
    fig = plt.figure(figsize=(FULL, 2.8))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 48)
    ax.axis("off")

    def box(x, y, w, h, title, body, edge, dy=7.6, fc="white"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc=fc, ec=edge, lw=1.1))
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=7.5,
                fontweight="bold")
        if body:
            ax.text(x + w / 2, y + h - dy, body, ha="center", va="top", fontsize=7,
                    linespacing=1.2)

    def arrow(x0, y0, x1, y1, c=INK, ls="-"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0,
                                    linestyle=ls))

    top, h = 25.0, 22.0
    boxes = [(1, 16), (20, 22.5), (46.5, 22.5), (73, 26)]
    texts = [("Foundation\npotential",
              "MACE-MP-0\n(medium, small)\nreplaced by\nMACE-MPA-0\n(medium)"),
             ("Atomistic\ncalculations",
              "relaxed defect energies\n(where carbon goes,\nGe around SiC);\nmolecular-dynamics\nconductivity"),
             ("Scattering model\nand surrogates",
              "phonon modes with\npoint-defect and\nSiC-particle scattering;\nfitted surrogates and\nmulti-fidelity models"),
             ("Decisions and\nconclusions",
              "recipe pick (Ge, C, SiC size);\nGe saving at equal\nconductivity; batch-design\nverdicts; composition pick\nat 1100 K; cost plans")]
    for (x, w), (t, b) in zip(boxes, texts):
        box(x, top, w, h, t, b, INK)
    for (x0, w0), (x1, _) in zip(boxes[:-1], boxes[1:]):
        arrow(x0 + w0 + 0.8, top + h / 2, x1 - 0.8, top + h / 2)

    sx, sw, sy, sh = 13, 60, 12.2, 8.6
    box(sx, sy, sw, sh, "Sources outside the potential",
        "Tersoff molecular dynamics; DFT phonon Boltzmann transport;\npublished and compiled measurements",
        OTHER, dy=4.4)
    arrow(58, sy + sh + 0.5, 58, top - 0.6, OTHER)
    arrow(64, sy + sh + 0.5, 80, top - 0.6, OTHER)

    # the campaign record: a strip under the chain that every step writes to
    ry, rh = 1.2, 7.0
    ax.add_patch(FancyBboxPatch((1, ry), 98, rh, boxstyle="round,pad=0.4,rounding_size=1.0",
                                fc=LIGHT, ec=GREY, lw=0.8))
    ax.text(50, ry + rh / 2, "Campaign record: entries with output digests, analysis code and manuscript "
            "lines state which step read which output", ha="center", va="center", fontsize=7)
    for x in (1 + 16 / 2, 73 + 26 / 2):
        ax.plot([x, x], [top - 0.6, ry + rh + 0.5], color=GREY, lw=0.8, ls=":")
    ax.plot([sx + sw / 2, sx + sw / 2], [sy - 0.5, ry + rh + 0.5], color=GREY, lw=0.8, ls=":")
    save(fig, "fig1_chain")


# ---------------------------------------------------------------- ESI Fig. S1
def fig_reach():
    d = load("p5_reach/reach_prediction.json")
    tiers = d["reach_by_tier"]
    order = ["T0_explicit", "T1_plus_prose_citations", "T2_plus_file_paths", "T3_plus_campaign_names"]
    labels = ["explicit links", "+ citations in free text",
              "+ shared analysis code", "+ shared campaign names"]
    n = [tiers[k]["n_entries"] for k in order]
    total = d["ledger_read"]["n_entries"]
    fig, ax = plt.subplots(figsize=(4.2, 1.7))
    y = np.arange(len(n))[::-1]
    prev = 0
    for yi, ni in zip(y, n):
        ax.barh(yi, prev, color="#C8C8C8", height=0.6)
        ax.barh(yi, ni - prev, left=prev, color=INK, height=0.6)
        ax.text(ni + 1.5, yi, f"{ni}", va="center", fontsize=7)
        prev = ni
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, total)
    ax.set_xlabel(f"record entries reached (of {total})")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color="#C8C8C8", label="reached at an earlier level"),
                       Patch(color=INK, label="added at this level")], loc="upper right")
    save(fig, "figS1_reach")


# ---------------------------------------------------------------- Fig. 2
def fig_defects():
    old = load("nano_sigec/m1c/m1c_summary.json")["per_x"]
    new = load("p5_reach/recompute/m1c_mpa_summary.json")["per_x"]
    zone = load("p5_reach/recompute/zone_mpa_results.json")["profile_dE_eV"]
    fig, axs = plt.subplots(1, 3, figsize=(FULL, 2.35))
    xs = ["0", "0.2", "0.5"]
    xv = np.array([0, 0.2, 0.5])
    ncfg = {len(s[k]["dE_prec_eV"]) for s in (old, new) for k in xs}
    nsite = {len(s[k]["site_pref"]) for s in (old, new) for k in ("0.2", "0.5")}
    assert ncfg == {3} and nsite == {3}, (ncfg, nsite)
    # (a) energy gained by carbon leaving the lattice as SiC
    ax = axs[0]
    for summ, c, lab, off in [(old, OLD, "MACE-MP-0", -0.012), (new, NEW, "MACE-MPA-0", 0.012)]:
        vals = [summ[k]["dE_prec_eV"] for k in xs]
        mean = np.array([np.mean(v) for v in vals])
        lo = mean - np.array([min(v) for v in vals])
        hi = np.array([max(v) for v in vals]) - mean
        ax.errorbar(xv + off, mean, yerr=[lo, hi], fmt="o-", color=c, ms=3.5, capsize=2, label=lab)
    ax.axhline(-0.5, color=INK, ls="--", lw=0.8)
    ax.text(0.5, -0.56, "registered threshold", ha="right", va="top", fontsize=7)
    ax.text(0.02, 0.99, "bars: range of 3\nconfigurations", transform=ax.transAxes, fontsize=7,
            va="top")
    ax.set_xlabel("Ge fraction $x$ of the host")
    ax.set_ylabel("$\\Delta E_\\mathrm{prec}$ (eV per C)")
    ax.set_ylim(-2.7, 0.0)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.6))
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
    ax.axhline(0, color=INK, ls="--", lw=0.8)
    ax.text(0.59, 0.012, "no site preference", ha="right", va="bottom", fontsize=7)
    ax.text(0.12, 0.47, "bars: range of 3\nconfigurations", fontsize=7, va="top")
    ax.set_xlim(0.1, 0.6)
    ax.set_xticks([0.2, 0.5])
    ax.set_xlabel("Ge fraction $x$ of the host")
    ax.set_ylabel("$\\Delta E_\\mathrm{site}$ (eV)")
    ax.set_ylim(-0.05, 0.5)
    panel(ax, "b")
    # (c) Ge segregation energy around a SiC particle, with the far-site scatter
    ax = axs[2]
    far = ["9.5", "10.5", "11.5", "12.5", "13.5"]
    for key, c, lab in [("MP-0", OLD, "MACE-MP-0"), ("MPA-0", NEW, "MACE-MPA-0")]:
        fv = np.array([zone[key][b] for b in far])
        m, s = fv.mean(), fv.std(ddof=1)
        ax.axhspan(m - s, m + s, color=c, alpha=0.13, lw=0)
        dd = sorted((float(k), v) for k, v in zone[key].items())
        ax.plot([a for a, _ in dd], [b for _, b in dd], "o-", color=c, ms=3.5, label=lab)
    ax.axhline(0.01, color=INK, ls="--", lw=0.9)
    ax.axhline(0, color=INK, lw=0.5)
    ax.text(13.9, 0.016, "first-shell threshold", ha="right", va="bottom", fontsize=7)
    ax.set_xlim(6.0, 14.0)
    ax.set_xlabel("distance to SiC centre (Å)")
    ax.set_ylabel("Ge segregation energy (eV)")
    ax.set_ylim(-0.19, 0.08)
    ax.legend(handles=[Patch(color=GREY, alpha=0.35, label="far-site mean ± 1 s.d.")],
              loc="lower right")
    panel(ax, "c")
    save(fig, "fig2_defects")


# ---------------------------------------------------------------- Fig. 3
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
    st = load("p5_reach/stats/stats_results.json")["T5_md_conductivity"]
    med = st["median_ratio"]
    ci_lo, ci_hi = st["median_ratio_ci95_bootstrap"]
    o3 = load("p3_mace/results/p3_mace_results.json")
    n3 = load("p5_reach/recompute/gpu/analysis/p3_mpa_results.json")
    so, sn = o3["scores"], n3["scores"]
    noise = list(o3["noise_floor_abs_log_diff"]) + list(n3["noise_floor_abs_log_diff"])
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 2.6), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    markers = {300: "o", 700: "s", 1100: "^"}
    for T, m in markers.items():
        r = [x for x in rows if x["T"] == T]
        ax.scatter([x["k_old"] for x in r], [x["k_new"] for x in r], marker=m, s=13,
                   color=TCOL[T], lw=0, alpha=0.9, label=f"{T} K", zorder=3)
    lim = np.array([0.25, 2.2])
    ax.plot(lim, lim, color=GREY, lw=0.8, ls="--", label="equal")
    ax.fill_between(lim, ci_lo * lim, ci_hi * lim, color=INK, alpha=0.3, lw=0, zorder=1)
    ax.plot(lim, med * lim, color=INK, lw=1.0, label=f"median ratio {med:.2f}", zorder=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(FixedLocator([0.3, 0.5, 1.0, 2.0]))
        axis.set_minor_locator(NullLocator())
        axis.set_major_formatter(FormatStrFormatter("%g"))
    ax.set_xlabel("$\\kappa$, MACE-MP-0 small (W m$^{-1}$ K$^{-1}$)")
    ax.set_ylabel("$\\kappa$, MACE-MPA-0 medium (W m$^{-1}$ K$^{-1}$)")
    ax.legend(loc="lower right", handlelength=1.4)
    panel(ax, "a")
    ax = axs[1]
    designs = [("CA1", "covering, 15 runs", "RND15"), ("OFAT", "one factor\nat a time, 12", "RND12"),
               ("CA2", "double covering, 30", None), ("RND_pool", "random, 30", None)]
    y = np.arange(len(designs))[::-1]
    ax.axvspan(min(noise), max(noise), color=LIGHT, lw=0, zorder=0)
    ax.text(0.5 * (min(noise) + max(noise)), len(designs) - 0.28, "repeat-seed difference",
            ha="center", va="top", fontsize=7)
    for yi, (k, lab, ref) in zip(y, designs):
        ax.plot([so[k]["log_rmse"], sn[k]["log_rmse"]], [yi, yi], color=GREY, lw=0.8, zorder=1)
        ax.scatter([so[k]["log_rmse"]], [yi], color=OLD, s=18, zorder=2)
        ax.scatter([sn[k]["log_rmse"]], [yi], color=NEW, s=18, zorder=2)
        if ref:
            for s, c, dy in [(so, OLD, 0.22), (sn, NEW, -0.22)]:
                q = s[ref]["log_rmse_q25_q75"]
                ax.plot(q, [yi + dy, yi + dy], color=c, lw=2.2, alpha=0.35, solid_capstyle="butt")
                ax.plot([s[ref]["log_rmse"]], [yi + dy], "|", color=c, ms=6)
    ax.set_yticks(y)
    ax.set_yticklabels([d[1] for d in designs])
    ax.set_xlabel("log RMSE on 16 hidden recipes")
    ax.set_xlim(0.05, 0.2)
    ax.set_ylim(-0.6, len(designs) - 0.25)
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=OLD, label="MACE-MP-0"),
                       Line2D([], [], ls="", marker="o", color=NEW, label="MACE-MPA-0"),
                       Line2D([], [], color=GREY, lw=2.2, alpha=0.5,
                              label="random batches\n(median, IQR)")],
              loc="lower right")
    panel(ax, "b")
    save(fig, "fig3_md")


# ---------------------------------------------------------------- Fig. 5
def _wall(pat, key="wall_s"):
    tot = 0.0
    for f in glob.glob(str(PROJECT / pat)):
        tot += json.load(open(f))[key]
    return tot / 3600


def _registered_gpu_estimate():
    s = load("p5_reach/recompute/gpu/gpu_design.json")["cost_estimate"]
    p4b = float(re.search(r"R_P4B .*?about (\d+) GPU-h", s).group(1))
    p3 = float(re.search(r"R_P3 .*?about (\d+) GPU-h", s).group(1))
    return p4b, p3


def _bars(ax, units, fmts, xmax, est=None):
    y = np.arange(len(units))[::-1]
    for i, (yi, (lab, o, n)) in enumerate(zip(y, units)):
        fmt = fmts[i]
        ax.barh(yi + 0.18, o, height=0.34, color=OLD)
        ax.barh(yi - 0.18, n, height=0.34, color=NEW)
        ax.text(o + 0.012 * xmax, yi + 0.18, fmt.format(o), va="center", fontsize=7)
        ax.text(n + 0.012 * xmax, yi - 0.18, fmt.format(n), va="center", fontsize=7)
        if est is not None:
            ax.plot([est[i]] * 2, [yi - 0.42, yi + 0.42], color=INK, lw=1.0, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels([u[0] for u in units])
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, len(units) - 0.4)
    ax.grid(axis="y", visible=False)


def fig_cost():
    cpu = [("defect energies\n51 relaxations", _wall("nano_sigec/m1c/out/*.json"),
            _wall("p5_reach/recompute/m1c/out/*.json")),
           ("Ge around SiC\n19 relaxations", _wall("nano_sigec/si_zone/chpc/out/*.json"),
            _wall("p5_reach/recompute/z1/out/*.json"))]
    g1 = ("conductivity offset\n2 MD runs", _wall("party4_mace/raw/*.json"),
          _wall("p5_reach/recompute/gpu/p4b/out/*.json"))
    g2 = ("SiGeC design space\n89 MD runs", _wall("p3_mace/raw/out/*.json", "wall_s_this_attempt"),
          _wall("p5_reach/recompute/gpu/p3/out/*.json", "wall_s_this_attempt"))
    gpu = [g1, g2, ("both GPU units", g1[1] + g2[1], g1[2] + g2[2])]
    e1, e2 = _registered_gpu_estimate()
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 2.3), gridspec_kw=dict(width_ratios=[1, 1.25]))
    ax = axs[0]
    _bars(ax, cpu, ["{:.2f}"] * 2, 3.6)
    ax.set_xlabel("CPU-task-hours per unit (16 cores)")
    panel(ax, "a")
    ax = axs[1]
    _bars(ax, gpu, ["{:.1f}", "{:.1f}", "{:.0f}"], 420, est=[e1, e2, e1 + e2])
    ax.set_xlabel("GPU-hours per unit")
    panel(ax, "b")
    fig.legend(handles=[Patch(color=OLD, label="MACE-MP-0 (recorded)"),
                        Patch(color=NEW, label="MACE-MPA-0 (measured)"),
                        Line2D([], [], color=INK, lw=1.0, ls="--",
                               label="GPU estimate registered before the runs")],
               loc="outside upper center", ncol=3)
    save(fig, "fig5_cost")


# ---------------------------------------------------------------- ESI Fig. S2
def fig_cards():
    rows = _p3_runs()
    cards = sorted({r["card_new"] for r in rows} | {r["card_old"] for r in rows},
                   key=lambda c: -np.median([r["h_new"] for r in rows if r["card_new"] == c] or [0]))
    fig, ax = plt.subplots(figsize=(4.2, 2.4))
    rng = np.random.default_rng(0)
    for i, c in enumerate(cards):
        ho = [r["h_old"] for r in rows if r["card_old"] == c]
        hn = [r["h_new"] for r in rows if r["card_new"] == c]
        if ho:
            ax.scatter(i - 0.17 + rng.uniform(-0.07, 0.07, len(ho)), ho, s=7, color=OLD, alpha=0.8, lw=0)
        if hn:
            ax.scatter(i + 0.17 + rng.uniform(-0.07, 0.07, len(hn)), hn, s=7, color=NEW, alpha=0.8, lw=0)
    ax.set_xticks(range(len(cards)))
    ax.set_xticklabels([c.replace("GeForce ", "").replace(" 40GB Active", "").replace("Tesla ", "")
                        for c in cards], rotation=35, ha="right")
    ax.set_ylabel("GPU-hours per MD run\n(1152 atoms)")
    ax.set_ylim(0, 9)
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=4, color=OLD, label="MACE-MP-0 small"),
                       Line2D([], [], ls="", marker="o", ms=4, color=NEW, label="MACE-MPA-0 medium")],
              loc="upper right")
    save(fig, "figS2_cards")


# ---------------------------------------------------------------- Fig. 4
# Registered thresholds (p5_reach/PREDICTION.md): precipitation -0.5 eV,
# first-shell flip +0.01 eV; sign thresholds (0) for the Ge trend and the
# site preference; the covering verdict holds while covering is worse than
# the random median of 15-run batches, the one-factor-at-a-time verdict while
# it is worse than the random median of 12-run batches. Scales: plausible
# version shift (reach_prediction.json) for energies, larger replicate-seed
# difference (p3_mace_results.json) for MD.
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

    def ofat(r):
        return r["scores"]["OFAT"]["log_rmse"] - r["scores"]["RND12"]["log_rmse"]

    rows = [("carbon leaves the lattice as SiC", prec(old), prec(new), d, "eV"),
            ("precipitation more favourable with Ge", trend(old), trend(new), d, "eV"),
            ("carbon prefers Si-rich shells", site(old), site(new), d, "eV"),
            ("SiC attracts Ge in the first shell", 0.01 - zone["MP-0"]["6.5"], 0.01 - zone["MPA-0"]["6.5"], d, "eV"),
            ("covering no better than random", cov(o3), cov(n3), noise, "(ln κ)"),
            ("one factor at a time worse than random", ofat(o3), ofat(n3), noise, "(ln κ)")]
    fig, ax = plt.subplots(figsize=(FULL, 2.4))
    ax.axvspan(-1, 1, color=LIGHT, zorder=0)
    ax.axvline(0, color=INK, lw=0.9)
    for i, (lab, a, b, sc, u) in enumerate(rows):
        ax.annotate("", xy=(b / sc, i), xytext=(a / sc, i),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9, shrinkA=3, shrinkB=3))
        ax.plot(a / sc, i, "o", color=OLD, ms=5, zorder=3)
        ax.plot(b / sc, i, "o", color=NEW, ms=5, zorder=3)
        ax.text(1.01, i, f"{sig2(a)} → {sig2(b)} {u}", fontsize=7,
                va="center", ha="left", color=INK, transform=ax.get_yaxis_transform())
    ax.plot([], [], "o", color=OLD, label="MACE-MP-0")
    ax.plot([], [], "o", color=NEW, label="MACE-MPA-0")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim(-0.8, 5.6)
    ax.set_xlabel("margin to the deciding threshold, in units of the plausible shift")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    save(fig, "fig4_margins")


if __name__ == "__main__":
    apply_style()
    fig_chain()
    fig_defects()
    fig_md()
    fig_cost()
    fig_margins()
    fig_reach()
    fig_cards()
