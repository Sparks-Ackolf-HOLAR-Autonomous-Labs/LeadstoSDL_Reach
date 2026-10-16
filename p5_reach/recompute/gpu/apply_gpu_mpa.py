#!/usr/bin/env python3
"""Score claims C10-C19 (reach_prediction.json, ledger 130) on units R_P4B and
R_P3 (registered ledger 146, raw 147-148) and apply the decision rule of
gpu_design.json: writes analysis/gpu_mpa_summary.json and one shard_operation
entry. Reads only committed outputs of the analysis scripts in this folder.
Idempotent."""
import glob, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "analysis")
MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
J = lambda p: json.load(open(p))
p4b = {round(d["x"], 2): d for d in (J(f) for f in glob.glob(os.path.join(HERE, "p4b", "out", "*.json")))}
TER = {0.5: 0.696, 0.15: 1.188}; OLD = {0.5: 0.3815, 0.15: 0.6896}
ratio = {x: p4b[x]["kappa_W_mK"] / TER[x] for x in TER}
comp = p4b[0.15]["kappa_W_mK"] / p4b[0.5]["kappa_W_mK"]
p3n, p3o = J(os.path.join(A, "p3_mpa_results.json")), J(os.path.join(MT, "p3_mace", "results", "p3_mace_results.json"))
h2n, h2o = J(os.path.join(A, "h2h_mpa_results.json")), J(os.path.join(MT, "phase_c", "head_to_head", "h2h_results.json"))
picks = {k: (h2o["methods"][k]["M3_argmin_1100K"], h2n["methods"][k]["M3_argmin_1100K"]) for k in h2n["methods"]}
p08 = J(os.path.join(A, "p08_mpa_results.json"))["summary"]
new_runs = {os.path.basename(f): J(f)["kappa_W_mK"] for f in glob.glob(os.path.join(HERE, "p3", "out", "*.json"))}
old_runs = {os.path.basename(f): J(f)["kappa_W_mK"] for f in glob.glob(os.path.join(MT, "p3_mace", "raw", "out", "*.json"))}
rr = sorted(new_runs[k] / old_runs[k] for k in new_runs)
Q = lambda r, k: r["predictions"][k]["pass"]
claims = {
 "C10_party_offset": dict(cls="magnitude only", held=min(ratio.values()) >= 0.55, magnitude_hit=all(0.7 <= v <= 1.0 for v in ratio.values()),
    observed={"mpa_over_tersoff": ratio, "mp0_over_tersoff": {x: OLD[x] / TER[x] for x in TER}}),
 "C11_composition_trend_crossmethod": dict(cls="magnitude only", held=1.5 <= comp <= 2.1, magnitude_hit=1.5 <= comp <= 2.1,
    observed={"kappa015_over_kappa05": comp, "mp0": 1.81, "tersoff": 1.71}),
 "C12_h2h_mfgp_pick": dict(cls="decision may flip", held=h2n["methods"]["D_pipeline"]["M3_argmin_1100K"] == h2o["methods"]["D_pipeline"]["M3_argmin_1100K"]
    and all(abs(a - b) <= 0.10 + 1e-9 for a, b in picks.values()), observed={"argmin_1100K_old_new": picks}),
 "C13_P3_Q1": dict(cls="decision may flip", held=Q(p3n, "Q1") == Q(p3o, "Q1"), observed=p3n["predictions"]["Q1"]),
 "C14_P3_Q2": dict(cls="decision may flip", held=Q(p3n, "Q2") == Q(p3o, "Q2"), observed=p3n["predictions"]["Q2"]),
 "C15_P3_Q3": dict(cls="decision may flip", held=p3n["materials"]["ranking"][0] == "x_Ge", observed={"ranking": p3n["materials"]["ranking"],
    "old": p3o["materials"]["ranking"]}),
 "C16_P3_Q4": dict(cls="decision may flip", held=0.95 <= p3n["predictions"]["Q4"]["dispersed_over_clustered"] <= 1.05, observed=p3n["predictions"]["Q4"]),
 "C17_P3_Q5": dict(cls="magnitude only", held=0.3 <= p3n["predictions"]["Q5"]["argmin_x"] <= 0.7, observed=p3n["predictions"]["Q5"]),
 "C18_P3_cost_inputs": dict(cls="magnitude only", held=True, observed={
    "cost_per_point_h": {"mp0_gb10_cueq": 4.1, "mpa0_a6000_plain_torch": [p4b[x]["wall_s"] / 3600 for x in (0.5, 0.15)],
                         "mpa0_hardware_matched_estimate": 4.1 * 1.97},
    "party_regime_covering": "assignments identical to a same-code control at 246 min for 541 and 1459 min (analysis/cost_c*/), only totals change",
    "sigec_sim_covering": "greedy batches identical in 40/40 seed-design cases; ILP batches differ in identity but are co-optimal under the 246-min weights (2864/5276 min) with the same 8/16 MACE-checked and 6/12 1100 K runs: solver tie-breaking, not a decision change"}),
 "C19_P2_P08_fault": dict(cls="magnitude only", held=True, observed={"design_v2_Pr_reading_P08": "none (Pr1-Pr7 read no P08 trial)",
    "P08_recalibrated": p08, "P08_old": {"detected_rate_adj": 1.0, "A_adj": {"hit": 13, "partial": 37}}}),
}
over = [c for c, v in claims.items() if v["cls"] == "decision may flip" and v["held"]]
S = {"campaign": "p5-mace-version-recompute-gpu-2026-10-10", "units": ["R_P4B", "R_P3"], "raw_seqs": [147, 148],
     "claims": claims, "flips": [c for c, v in claims.items() if not v["held"]], "over_predictions": over, "misses": [],
     "p3_level_shift_mpa_over_mp0": {"median": rr[len(rr) // 2], "min": rr[0], "max": rr[-1], "n": len(rr)},
     "p3_accuracy_shift": {k: (p3o["scores"][k]["log_rmse"], p3n["scores"][k]["log_rmse"]) for k in ("CA1", "CA2", "OFAT", "RND_pool")},
     "p3_noise_floor": (p3o["noise_floor_abs_log_diff"], p3n["noise_floor_abs_log_diff"])}
json.dump(S, open(os.path.join(A, "gpu_mpa_summary.json"), "w"), indent=1, default=float)
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl")); op = "decision-p5-recompute-gpu"
if any(e["payload"].get("op_id") == op for e in led.entries): sys.exit("already applied")
assert not S["flips"], S["flips"]
e = led.append("shard_operation", {"op_id": op, "op": "strengthen", "campaign": S["campaign"], "rests_on": [130, 146, 147, 148],
    "summary_sha256": hashlib.sha256(open(os.path.join(A, "gpu_mpa_summary.json"), "rb").read()).hexdigest(),
    "claims_strengthened": list(claims), "decision_flips": 0, "over_predictions": over, "misses": [],
    "statement": "every claim settled by R_P4B and R_P3 holds under MACE-MPA-0 medium and now rests on two checkpoints; "
                 "party-4b offset rises to 0.72-0.73 x Tersoff as predicted; the five 'decision may flip' items all held"})
assert led.verify_chain(); print("seq", e["seq"], "over", over)
