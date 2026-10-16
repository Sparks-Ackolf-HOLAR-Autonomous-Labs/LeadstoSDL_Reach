#!/usr/bin/env python3
"""Formal statistical tests for P5 (release MACE-MP-0 -> MACE-MPA-0).

Added on 2026-10-11 after the recompute was scored. The registered grades
(ledger 130-149) are not changed by anything here; the tests attach p-values,
confidence intervals and power statements to the hypotheses H1-H3 and to the
materials readings. Reads only committed files; writes stats_results.json.

T1  H1 no miss: exact Clopper-Pearson bound on the miss rate.
T2  H2 margin vs change: Fisher exact test, with the smallest p-value the
    design could reach (power statement).
T3  release shift of defect energies: paired tests per configuration against
    0 and against the assumed shift delta = 0.3 eV.
T4  first-shell segregation (the one reversed claim): each near bin tested
    against the scatter of the far bins (local-environment null).
T5  release shift of MD conductivity: Wilcoxon signed-rank on 89 paired runs,
    bootstrap CI of the median ratio, Kruskal-Wallis per factor (Holm).
T6  batch-design verdicts: empirical percentile of each design among the same
    200 random batches under both releases; Kendall tau of factor rankings.
T7  dispersed vs clustered carbon: Wilcoxon signed-rank on matched pairs.
"""
import json, math, os, random, sys
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))  # project root
P5 = os.path.join(MT, "p5_reach")
DELTA = 0.3  # registered plausible shift (eV), reach_prediction.json
rng_boot = np.random.default_rng(20261011)
R = {"note": "post hoc formal tests; registered grades unchanged", "delta_eV": DELTA}


def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = [0.0] * m; run = 0.0
    for i, j in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[j])); adj[j] = run
    return adj


# ---------- T1, T2: claim score ----------
pred = json.load(open(os.path.join(P5, "reach_prediction.json")))
unsettled = {"C20_theorist_O3", "C22_P4_T1_live", "C23_fault_study_chain",
             "C24_records_without_mace_quantity"}  # paper Section 4.5
changed = {"C8_zone_PrZ1"}
settled = [c for c in pred["claims"] if c["id"] not in unsettled]
flag = set(pred["decision_may_flip"])
n_set = len(settled)
n_unflag = sum(1 for c in settled if c["id"] not in flag)
n_flag = n_set - n_unflag
assert (n_set, n_flag) == (20, 9), (n_set, n_flag)
a, b = 1, n_flag - 1          # flagged: changed, held
c_, d = 0, n_unflag           # unflagged: changed, held
cp = lambda k, n: float(1 - 0.05 ** (1 / n)) if k == 0 else None  # one-sided 95 %
R["T1_H1_misses"] = {"settled": n_set, "unflagged_settled": n_unflag, "misses": 0,
                     "miss_rate_upper95_unflagged": cp(0, n_unflag),
                     "miss_rate_upper95_all_settled": cp(0, n_set)}
odds, p_f = stats.fisher_exact([[a, b], [c_, d]], alternative="greater")
p_min = n_flag / n_set  # best attainable one-sided p with a single change
R["T2_H2_fisher"] = {"table_flagged_changed_held": [a, b], "table_unflagged_changed_held": [c_, d],
                     "p_one_sided": float(p_f), "smallest_attainable_p_with_one_change": p_min,
                     "changes_needed_for_p_below_0.05": None}
for k in range(1, n_flag + 1):  # all k changes inside the flagged set
    if stats.fisher_exact([[k, n_flag - k], [0, n_unflag]], alternative="greater")[1] < 0.05:
        R["T2_H2_fisher"]["changes_needed_for_p_below_0.05"] = k; break

# ---------- T3: defect energies, paired per configuration ----------
def m1c(dirn):
    out = {}
    for f in os.listdir(dirn):
        if f.endswith(".json"):
            r = json.load(open(os.path.join(dirn, f))); out[r["task"]] = float(r["E_eV"])
    return out

old = m1c(os.path.join(MT, "nano_sigec", "m1c", "out"))
new = m1c(os.path.join(P5, "recompute", "m1c", "out"))
so = json.load(open(os.path.join(MT, "nano_sigec", "m1c", "m1c_summary.json")))
sn = json.load(open(os.path.join(P5, "recompute", "m1c_mpa_summary.json")))
prec = {"old": [], "new": []}; site = {"old": [], "new": []}
for x in ("0", "0.2", "0.5"):
    for tag, s in (("old", so), ("new", sn)):
        prec[tag] += list(s["per_x"][x]["dE_prec_eV"])
        site[tag] += [p["dE_site"] for p in s["per_x"][x].get("site_pref", [])]
dp = np.array(prec["new"]) - np.array(prec["old"])
ds = np.array(site["new"]) - np.array(site["old"])
def paired(dv, label):
    w0 = stats.wilcoxon(dv) if len(dv) >= 5 else None
    t0 = stats.ttest_1samp(dv, 0.0)
    tD = stats.ttest_1samp(np.abs(dv), DELTA, alternative="greater")
    wD = stats.wilcoxon(np.abs(dv) - DELTA, alternative="greater")
    se = dv.std(ddof=1) / math.sqrt(len(dv))
    tq = stats.t.ppf(0.975, len(dv) - 1)
    return {"quantity": label, "n_pairs": int(len(dv)), "mean_shift_eV": float(dv.mean()),
            "ci95_eV": [float(dv.mean() - tq * se), float(dv.mean() + tq * se)],
            "t_vs_0": {"t": float(t0.statistic), "p": float(t0.pvalue)},
            "wilcoxon_vs_0_p": float(w0.pvalue) if w0 else None,
            "abs_shift_gt_delta": {"t": float(tD.statistic), "p_t": float(tD.pvalue),
                                   "p_wilcoxon_exact": float(wD.pvalue)}}
R["T3_defect_energies"] = {"precipitation_energy": paired(dp, "dE_prec per configuration"),
                           "site_preference": paired(ds, "dE_site per configuration")}
# site preference: test |shift| < delta instead (equivalence direction)
R["T3_defect_energies"]["site_preference"]["abs_shift_lt_delta_p_t"] = float(
    stats.ttest_1samp(np.abs(ds), DELTA, alternative="less").pvalue)

# ---------- T4: first-shell segregation ----------
# The two sites of each bin are symmetry copies (energies equal to 1e-11 eV), so
# they carry no noise estimate. The null is the scatter of dE over the bins at
# 9.5-13.5 A, beyond the reach of the particle strain field, which samples how
# much the local alloy environment alone moves a Ge site energy. Each near bin
# is tested as one new draw from that distribution (prediction-interval t-test).
def zone(dirn):
    rows = [json.load(open(os.path.join(dirn, f))) for f in sorted(os.listdir(dirn))
            if f.endswith(".json") and f != "ref.json"]
    e_far = np.mean([float(r["E_eV"]) for r in rows if r["task"].startswith("far_")])
    bins = {}
    for r in rows:
        if r["task"].startswith("d"):
            bins.setdefault(float(r["task"][1:].split("_")[0]), []).append(float(r["E_eV"]) - e_far)
    de = {b: float(np.mean(v)) for b, v in sorted(bins.items())}
    far = np.array([v for b, v in de.items() if b >= 9.5])
    m, s, n = far.mean(), far.std(ddof=1), len(far)
    out = {"null_bins_A": [b for b in de if b >= 9.5], "null_mean_eV": float(m), "null_sd_eV": float(s),
           "df": n - 1, "site_copy_max_diff_eV": float(max(max(v) - min(v) for v in bins.values()))}
    for b in (6.5, 7.5, 8.5):
        t = (de[b] - m) / (s * math.sqrt(1 + 1 / n))
        out[f"bin_{b}"] = {"dE_eV": de[b], "t": float(t), "p_two_sided": float(2 * stats.t.sf(abs(t), n - 1))}
    for b, ph in zip((6.5, 7.5, 8.5), holm([out[f"bin_{b}"]["p_two_sided"] for b in (6.5, 7.5, 8.5)])):
        out[f"bin_{b}"]["p_holm"] = ph
    return out
R["T4_first_shell"] = {"MACE-MP-0": zone(os.path.join(MT, "nano_sigec", "si_zone", "chpc", "out")),
                       "MACE-MPA-0": zone(os.path.join(P5, "recompute", "z1", "out"))}

# ---------- T5: MD conductivity shift ----------
def kap(dirn):
    return {f[:-5]: json.load(open(os.path.join(dirn, f))) for f in os.listdir(dirn) if f.endswith(".json")}
ko = kap(os.path.join(MT, "p3_mace", "raw", "out"))
kn = kap(os.path.join(P5, "recompute", "gpu", "p3", "out"))
ids = sorted(set(ko) & set(kn))
lr = np.array([math.log(kn[i]["kappa_W_mK"] / ko[i]["kappa_W_mK"]) for i in ids])
w = stats.wilcoxon(lr)
boot = np.median(rng_boot.choice(lr, (10000, len(lr))), axis=1)
facs = {"x_Ge": "x_Ge", "y_C": "y_C", "carbon_form": "carbon_form", "dopant": "dopant", "T_K": "T_K"}
kw = {}
for f in facs:
    lev = {}
    for i, v in zip(ids, lr):
        lev.setdefault(str(ko[i][f]), []).append(v)
    kw[f] = {"levels": {k: [len(v), float(np.exp(np.median(v)))] for k, v in sorted(lev.items())},
             "H": float(stats.kruskal(*lev.values()).statistic), "p": float(stats.kruskal(*lev.values()).pvalue)}
adj = holm([kw[f]["p"] for f in facs])
for f, p in zip(facs, adj):
    kw[f]["p_holm"] = p
rep = json.load(open(os.path.join(P5, "recompute", "gpu", "analysis", "p3_mpa_results.json")))["noise_floor_abs_log_diff"]
R["T5_md_conductivity"] = {"n_pairs": len(ids), "median_ratio": float(np.exp(np.median(lr))),
                           "ratio_range": [float(np.exp(lr.min())), float(np.exp(lr.max()))],
                           "median_ratio_ci95_bootstrap": [float(np.exp(np.quantile(boot, 0.025))),
                                                           float(np.exp(np.quantile(boot, 0.975)))],
                           "wilcoxon_signed_rank": {"W": float(w.statistic), "p": float(w.pvalue)},
                           "fraction_ratio_gt_1": float(np.mean(lr > 0)),
                           "sd_log_ratio": float(lr.std(ddof=1)),
                           "replicate_abs_log_diff_MPA": rep,
                           "kruskal_wallis_per_factor": kw}

# ---------- T6: design verdicts under both releases ----------
sys.path.insert(0, os.path.join(MT, "p3_mace"))
import analyze_p3_mace as A  # noqa: E402  (checks its design hash on import)
import design_p3_mace as D  # noqa: E402


def design_scores(outdir):
    A.OUT = outdir
    k, _ = A.load()
    hidden = [tuple(r) for r in A.HID["hidden"] if "H_" + D.pid(tuple(r)) in k]
    des = {n: [tuple(r) for r in v] for n, v in A.DES.items()}
    S = {n: A.score(des[n], k, hidden)["log_rmse"] for n in ("CA1", "CA2", "OFAT", "RND_pool")}
    rng = random.Random(64)  # same draws as the registered analysis
    pool = [r for r in des["RND_pool"] if D.pid(r) in k]
    dist = {}
    for n, size in (("RND15", 15), ("RND12", 12)):
        dist[n] = [A.score(rng.sample(pool, size), k, hidden)["log_rmse"] for _ in range(200)]
    return S, dist

T6 = {}
for tag, od in (("MACE-MP-0", os.path.join(MT, "p3_mace", "raw", "out")),
                ("MACE-MPA-0", os.path.join(P5, "recompute", "gpu", "p3", "out"))):
    S, dist = design_scores(od)
    T6[tag] = {"log_rmse": S,
               "RND15_median": float(np.median(dist["RND15"])), "RND12_median": float(np.median(dist["RND12"])),
               # one-sided empirical p for "design better than random": share of random batches at or below it
               "p_CA1_better_than_random15": float((np.sum(np.array(dist["RND15"]) <= S["CA1"]) + 1) / 201),
               "p_CA2_better_than_random15": float((np.sum(np.array(dist["RND15"]) <= S["CA2"]) + 1) / 201),
               "p_OFAT_worse_than_random12": float((np.sum(np.array(dist["RND12"]) >= S["OFAT"]) + 1) / 201)}
    T6[tag]["_dist"] = dist
d_old, d_new = T6["MACE-MP-0"].pop("_dist"), T6["MACE-MPA-0"].pop("_dist")
rho = stats.spearmanr(d_old["RND15"] + d_old["RND12"], d_new["RND15"] + d_new["RND12"])
T6["same_200_batches_rank_corr_across_release"] = {"spearman": float(rho.statistic), "p": float(rho.pvalue)}
ro = json.load(open(os.path.join(MT, "p3_mace", "results", "p3_mace_results.json")))["materials"]["ranking"]
rn = json.load(open(os.path.join(P5, "recompute", "gpu", "analysis", "p3_mpa_results.json")))["materials"]["ranking"]
tau = stats.kendalltau([ro.index(f) for f in ro], [rn.index(f) for f in ro], alternative="greater")
T6["factor_ranking"] = {"old": ro, "new": rn, "kendall_tau": float(tau.statistic), "p_exact_one_sided": float(tau.pvalue)}
R["T6_design_verdicts"] = T6

# ---------- T7: dispersed vs clustered carbon ----------
T7 = {}
for tag, f in (("MACE-MP-0", os.path.join(MT, "p3_mace", "results", "p3_mace_results.json")),
               ("MACE-MPA-0", os.path.join(P5, "recompute", "gpu", "analysis", "p3_mpa_results.json"))):
    pr = np.log(json.load(open(f))["materials"]["dispersed_over_clustered_matched_pairs"])
    wt = stats.wilcoxon(pr)
    se = pr.std(ddof=1) / math.sqrt(len(pr)); tq = stats.t.ppf(0.975, len(pr) - 1)
    T7[tag] = {"n_pairs": int(len(pr)), "geo_mean_ratio": float(np.exp(pr.mean())),
               "ci95_ratio": [float(np.exp(pr.mean() - tq * se)), float(np.exp(pr.mean() + tq * se))],
               "wilcoxon_p": float(wt.pvalue)}
R["T7_carbon_form"] = T7

json.dump(R, open(os.path.join(HERE, "stats_results.json"), "w"), indent=1)
print(json.dumps(R, indent=1))
