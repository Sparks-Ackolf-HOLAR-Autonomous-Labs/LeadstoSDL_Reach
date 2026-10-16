#!/usr/bin/env python3
"""Apply the registered Si-depleted-zone decision (zone_design.json, ledger seq 62) after
analyze_zone.py: one shard_operation entry for the branch the rule selects, plus the
refuted prediction recorded as refuted. Raw outputs were ledgered first (seq 69)."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(MT, "pilot", "src"))
from ledger import Ledger  # noqa: E402

RF = os.path.join(HERE, "zone_results.json")
R = json.load(open(RF))
D = json.load(open(os.path.join(HERE, "zone_design.json")))
led = Ledger(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"))
op_id = "si-zone-decision-2026-09-30"
if any(e["payload"].get("op_id") == op_id for e in led.entries):
    sys.exit("already applied")
br = R["decision"]["branch"]
prof = {str(p["bin"]): round(p["dE_mean"], 4) for p in R["Z1"]["profile"]}
e = led.append("shard_operation", {
    "op_id": op_id, "campaign": D["campaign"], "op": br,
    "target": {"claims": ["few-nm SiC kappa reduction at the density edge (ledger seq 61)",
                          "equal-kappa Ge saving 27-33% (ledger seq 61)"]},
    "cause": f"registered rule: cancel = {R['decision']['cancel']} at R = 2.5, 5 nm (< 0.2 at both); "
             f"gates G1-G3 pass; w_eq(1473 K) = {R['Z1']['w_eq_A_1473K']} A",
    "decision": {"by": "rule (pre-registered), applied by agent", "rule": R["decision"]["rule"]},
    "effect": "carbon claims stand at the seq-61 values; the Si-rich zone is recorded as a quantified "
              "minor term: MACE finds no equilibrium Ge depletion around a SiC particle in Si "
              "(Ge is attracted to the interface region, dE = -0.09 eV at 6.5 A, -0.07 eV at 7.5 A), "
              "so the zone imposed in the parent MD check (ledger 59-61) is not an equilibrium feature; "
              f"a depleted zone would need w* = {R['Z3']['rows']['R2.5nm']['w_star_A']:.0f} A (R 2.5 nm) or "
              f"{R['Z3']['rows']['R5nm']['w_star_A']:.0f} A (R 5 nm) to erase the benefit",
    "refuted": {"PrZ1": "predicted dE > 0 at 6.5 A (SiC repels Ge); observed "
                        f"{R['PrZ1']['dE_innermost_eV']:.3f} eV (attraction). Kept as refuted."},
    "held": ["PrZ2", "PrZ3", "PrZ4"],
    "evidence": {"raw_batch": "ledger seq 69", "results_file": "nano_sigec/si_zone/zone_results.json",
                 "results_sha256": hashlib.sha256(open(RF, "rb").read()).hexdigest(),
                 "dE_profile_eV": prof},
    "disclosed": "the two sites per distance bin turned out to be symmetry-equivalent (energies equal to "
                 "1e-11 eV), so the within-bin noise estimate is degenerate and the fixed 0.01 eV floor "
                 "decided significance; the Z1 host is dilute Ge in pure Si, not Si0.8Ge0.2"})
assert led.verify_chain()
print("seq", e["seq"], br)
