#!/usr/bin/env python3
"""Apply the ledger-133 decision rule to unit R_M1C (claims C1-C5, C20/O3)
from m1c_mpa_summary.json. One shard_operation entry. Idempotent."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
S = json.load(open(os.path.join(HERE, "m1c_mpa_summary.json")))
sc = S["claim_scores"]
shift = S["predictions"]["PM2"]["shift_eV"]
o3 = "sign holds, magnitude changes by more than 0.3 eV" if all(abs(v) > 0.3 for v in shift.values()) else "sign holds, magnitude within 0.3 eV"
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
op = "decision-p5-recompute-m1c"
if any(e["payload"].get("op_id") == op for e in led.entries):
    sys.exit("already applied")
e = led.append("shard_operation", {
    "op_id": op, "op": "strengthen", "campaign": "p5-mace-version-recompute-cpu-2026-10-09", "rests_on": [130, 133, 134],
    "summary_sha256": hashlib.sha256(open(os.path.join(HERE, "m1c_mpa_summary.json"), "rb").read()).hexdigest(),
    "claims_strengthened": ["C1_lattice_gate", "C2_carbon_leaves_lattice", "C3_carbon_trend_with_Ge",
                            "C4_carbon_prefers_Si_rich_shells", "C5_size_misfit_delta_C"],
    "decision_flips": 0,
    "reach_scoring": {"C1": "decision held (over-predicted as may-flip); predicted Ge +1.5 to +2.5 %, observed +1.08 %: magnitude miss",
                      "C2": "held as predicted (magnitude only); predicted shift 0.05-0.3 eV, observed 0.65-0.75 eV: magnitude miss",
                      "C3": "decision held (over-predicted); difference -0.35 eV inside predicted 0.1-0.4",
                      "C4": "decision held (over-predicted); dE_site 0.24/0.39 eV inside predicted 0.1-0.4",
                      "C5": "not refuted (within 30 % of Vegard); predicted within 10 % of -0.394, observed 10-14 % below: magnitude miss"},
    "o3_outcome": o3, "o3_grades": {"A_sonnet": "category right (value 1.3 eV vs 2.08-2.43 eV)", "B_haiku": "category wrong",
                                    "C_theorizer": "no basis", "reach_prediction_C20": "refuted (predicted B's category)"},
    "statement": "every MACE-dependent decision in R_M1C holds under MACE-MPA-0 (now rests on two checkpoints); the record's 0.3 eV plausible-shift bound was too small (observed 0.65-0.75 eV on dE_prec)"})
assert led.verify_chain()
print("seq", e["seq"], o3)
