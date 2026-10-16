#!/usr/bin/env python3
"""Depleted-zone width that would cancel the SiC benefit, at each contrast.

P1 (Strengths and limitations, "The Si-rich zone rests on a small particle")
quotes the width w* of a fully Ge-depleted (pure Si) shell around each SiC
particle at which the shell's added conduction cancels the particle's
kappa_L reduction. analyze_zone.py computed w* once, at the density-edge
contrast that was current when the zone check was registered (ledger 62).
The contrast was later measured as a function of radius (ledger 110), which
lowers the particle reduction and so the width needed to cancel it. This
script recomputes w* with the registered machinery for both contrasts:

  * composite rule: Maxwell-Garnett, pure-Si pockets with contrast c in the
    alloy matrix (c from zone_results.json, the value the registered
    analysis used);
  * pocket fraction f_p = phi * ((R + w)^3 - R^3) / R^3, phi = SiC volume
    fraction at 1 at% C (zone_design.json, stage Z3);
  * cancel = (MG(f_p, c) - 1) / r_particle; w* solves cancel = 1;
  * r_particle at the density edge: small_sic/decision_robustness.json (the
    density-edge row of the contrast sweep, 300 and 1100 K);
  * r_particle at the measured contrast: small_sic/r50/measured_curves.json
    (Si0.8Ge0.2, 0.3 um effective grains, 300 K, 1 at% C).

The same bisection as analyze_zone.py is used, so the density-edge widths
reproduce zone_results.json (checked below). Treating the zone as pure Si
makes MG an upper bound on its effect, so each w* is a lower bound on the
width a processing route would need to create before the benefit is lost.

Output: zone_widths.json. Run: python3 zone_widths.py (no arguments).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = os.path.join(HERE, "..", "small_sic")
X_C = 0.01  # 1 at% C, the campaign recipe


def load(*p):
    with open(os.path.join(*p)) as f:
        return json.load(f)


def mg(f, c):
    """Maxwell-Garnett ratio, as in analyze_zone.py."""
    return (c + 2 + 2 * f * (c - 1)) / (c + 2 - f * (c - 1))


def w_star(R_A, r_part, phi, c):
    """Zone width (A) at which the pocket cancels the particle reduction."""
    lo, hi = 0.0, R_A * ((1 + 0.5 / phi) ** (1 / 3) - 1)  # f_pocket <= 0.5
    for _ in range(80):
        mid = (lo + hi) / 2
        g = mg(phi * ((R_A + mid) ** 3 - R_A ** 3) / R_A ** 3, c)
        lo, hi = (mid, hi) if (g - 1) / r_part < 1 else (lo, mid)
    return (lo + hi) / 2


def at_xc(curve, xc):
    for x, k in curve:
        if abs(x - xc) < 1e-12:
            return k
    raise KeyError(xc)


def main():
    design = load(HERE, "zone_design.json")
    zres = load(HERE, "zone_results.json")
    phi = design["stages"]["Z3"]["phi_SiC_at_1at_C"]
    c = zres["c_used"]["c"]

    dr = load(SMALL, "decision_robustness.json")
    lam_d = dr["lam2_brackets_x0.2"]["density"]
    row_d = min(dr["sweep"], key=lambda r: abs(r["lam2"] - lam_d))
    mc = load(SMALL, "r50", "measured_curves.json")
    k0 = mc["kappa_ref_x0.2_noC"]

    contrasts = {
        "density_edge": {
            "source": "small_sic/decision_robustness.json, density-edge row (ledger 61)",
            "r_particle": {T: {R: row_d[f"red_pct_R{R}_T{T}"] / 100 for R in ("2.5", "5")}
                           for T in ("300", "1100")},
        },
        "measured": {
            "source": "small_sic/r50/measured_curves.json (ledger 110), 300 K",
            "r_particle": {"300": {R: 1 - at_xc(mc["panel_a_x0.2"][f"R{R}"], X_C) / k0
                                   for R in ("2.5", "5")}},
        },
    }

    out = {"c": c, "phi_SiC_at_1at_C": phi, "x_C": X_C,
           "bound": "pure-Si zone: each w* is a lower bound on the width needed to cancel",
           "rows": {}}
    for name, spec in contrasts.items():
        rows = {}
        for T, per in spec["r_particle"].items():
            for R, rp in per.items():
                w = w_star(float(R) * 10, rp, phi, c)
                rows[f"R{R}nm_T{T}K"] = {"r_particle": rp, "w_star_A": w, "w_star_nm": w / 10}
        out["rows"][name] = {"source": spec["source"], "widths": rows}

    # the density-edge 300 K widths must reproduce the registered analysis
    reg = zres["Z3"]["rows"]
    for R in ("2.5", "5"):
        mine = out["rows"]["density_edge"]["widths"][f"R{R}nm_T300K"]["w_star_A"]
        assert abs(mine - reg[f"R{R}nm"]["w_star_A"]) < 0.05, (R, mine, reg[f"R{R}nm"]["w_star_A"])
    out["check"] = "density-edge 300 K widths reproduce zone_results.json Z3 w_star_A"

    with open(os.path.join(HERE, "zone_widths.json"), "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for name, blk in out["rows"].items():
        for k, v in blk["widths"].items():
            print(f"{name:13s} {k:14s} r={v['r_particle']*100:5.2f}%  w*={v['w_star_nm']:.2f} nm")


if __name__ == "__main__":
    main()
