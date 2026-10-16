#!/usr/bin/env python3
"""Apply the ledger-133 decision rule to unit R_Z1 (claims C8, C9) from
zone_mpa_results.json. C8 flipped under its refuted_if, so: scope_limit to
'MACE-MP-0 only' plus flag on the dependent paper statements (no paper text
changes at this step). C9 held: strengthen. Idempotent."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402
F = os.path.join(HERE, "zone_mpa_results.json")
S = json.load(open(F))
c8, c9 = S["claim_scores"]["C8"], S["claim_scores"]["C9"]
assert c8["refuted"] and not c9["refuted"], "rule branch changed; edit before applying"
sha = hashlib.sha256(open(F, "rb").read()).hexdigest()
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
if any(e["payload"].get("op_id") == "decision-p5-recompute-z1-c8" for e in led.entries):
    sys.exit("already applied")
camp = "p5-mace-version-recompute-cpu-2026-10-09"
e1 = led.append("shard_operation", {
    "op_id": "decision-p5-recompute-z1-c8", "op": "scope_limit", "campaign": camp, "rests_on": [69, 70, 130, 133, 137],
    "summary_sha256": sha, "claim": "C8_zone_PrZ1",
    "new_scope": "MACE-MP-0 only",
    "evidence": {"dE_6.5A_MP0_eV": c8["dE_innermost_old_eV"], "dE_6.5A_MPA0_eV": c8["dE_innermost_new_eV"],
                 "refuted_if": "dE(6.5 A) > +0.01 eV", "margin_eV": c8["dE_innermost_new_eV"] - 0.01},
    "flags": ["P1 draft.tex SiGeC zone paragraph: 'a Ge atom is 0.09 eV lower ... 1.5 A outside the particle'",
              "P2 draft.tex entry 62 paragraph: 'SiC was expected to repel Ge; it attracts it'"],
    "reach_scoring": {"C8": c8["score"]},
    "statement": "the innermost-shell Ge attraction at a SiC particle (PrZ1 refuted under MACE-MP-0) does not hold under MACE-MPA-0 "
                 "(+0.010 eV, neutral within 0.4 meV of the threshold; the strongest attraction moves to 8.5 A, -0.16 eV); "
                 "the verdict is limited to MACE-MP-0 and the dependent statements are flagged; paper text unchanged pending operator decision"})
e2 = led.append("shard_operation", {
    "op_id": "decision-p5-recompute-z1-c9", "op": "strengthen", "campaign": camp, "rests_on": [70, 130, 133, 137],
    "summary_sha256": sha, "claims_strengthened": ["C9_zone_decision"],
    "evidence": {"cancel_MP0": c9["cancel_old"], "cancel_MPA0": c9["cancel_new"],
                 "w_eq_1473K_A": [c9["w_eq_1473K_old_A"], c9["w_eq_1473K_new_A"]]},
    "reach_scoring": {"C9": c9["score"]},
    "statement": "no equilibrium Ge-depleted zone forms under either checkpoint (w_eq = 0 at 1473 K, cancel 0.00 at R = 2.5 and 5 nm); the carbon claims rest on two checkpoints"})
assert led.verify_chain()
print("seq", e1["seq"], e2["seq"])
