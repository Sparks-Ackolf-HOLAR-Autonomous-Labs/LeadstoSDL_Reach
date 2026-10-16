#!/usr/bin/env python3
"""Compare the SiGeC analyses rerun on the MACE-MPA-0 summary (sigec_mpa/) with the committed
MACE-MP-0 results and score claims C6, C7, C21 of ../reach_prediction.json by their refuted_if."""
import filecmp, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); NS = os.path.join(HERE, "..", "..", "nano_sigec")
pairs = {"sigec_results_m1c": "results/sigec_results_m1c.json", "decision_robustness": "small_sic/decision_robustness.json",
         "r50_results": "small_sic/r50/r50_results.json", "light_dopants_results": "light_dopants/light_dopants_results.json"}
same = {k: filecmp.cmp(os.path.join(HERE, "sigec_mpa", f"{k}_mpa.json"), os.path.join(NS, v), shallow=False) for k, v in pairs.items()}
a = json.load(open(os.path.join(NS, pairs["sigec_results_m1c"])))
b = json.load(open(os.path.join(HERE, "sigec_mpa", "sigec_results_m1c_mpa.json")))
changed = sorted(k for k in a if a[k] != b.get(k))
sub = [abs(y["sub_eps39"] - x["sub_eps39"]) / abs(x["sub_eps39"]) for x, y in zip(a["D3_lever_pct_at_yC_0.01"], b["D3_lever_pct_at_yC_0.01"]) if x.get("sub_eps39")]
out = {"byte_identical": same, "sigec_results_keys_changed": changed,
       "screening_pick_identical": a["D4_screening"] == b["D4_screening"], "checks_identical": a["checks"] == b["checks"],
       "substitutional_strain_bound_rel_change": [min(sub), max(sub)],
       "claim_scores": {
           "C6": "held as predicted (magnitude only): pick identical (x = 0.3, 3 at% C, few-nm SiC), decision_robustness.json byte-identical",
           "C7": "held as predicted (unaffected): r50_results.json byte-identical, ledger-110 savings unchanged to the last digit",
           "C21": "held as predicted (unaffected): light_dopants_results.json byte-identical"}}
assert same["decision_robustness"] and same["r50_results"] and same["light_dopants_results"] and out["screening_pick_identical"]
json.dump(out, open(os.path.join(HERE, "sigec_mpa", "comparison.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "claim_scores"}, indent=1))
