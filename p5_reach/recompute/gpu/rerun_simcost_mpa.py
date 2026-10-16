#!/usr/bin/env python3
"""Claim C18 test, part 2: the SiGeC simulation-evidence cost model
(p3_limits/cost_models.py, Sim) charges 246 min per MACE-MD check point. Rebuild
the cost-weighted greedy covering batches (20 seeds, single and doubled, exactly
as p3_limits/cost_covering.py) and the ILP batch with that constant replaced,
and compare the chosen runs with a same-code control at 246 min.
Usage: python rerun_simcost_mpa.py <cost_min> <tag>"""
import json, os, sys, types
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PL = os.path.join(MT, "p3_limits"); sys.path.insert(0, PL)
cost, tag = float(sys.argv[1]), sys.argv[2]
import common as C
f = os.path.join(PL, "cost_models.py"); src = open(f).read()
a = "(246.0 if small_sic else 0.0)"; assert src.count(a) == 1; src = src.replace(a, "(%r if small_sic else 0.0)" % cost)
M = types.ModuleType("cost_models"); M.__file__ = f; sys.modules["cost_models"] = M
exec(compile(src, f + " [cost swap]", "exec"), M.__dict__)
sim = [m for m in M.MODELS if m.name == "simulation_evidence"][0]
SEEDS = range(20); out = {"cost_min": cost}
W1 = [C.greedy_cover(2, 1, s, cost=sim) for s in SEEDS]
W2 = [C.greedy_cover(2, 2, 1000 + s, cost=sim, base=W1[s]) for s in SEEDS]
out["greedy_single"] = [sorted(map(lambda r: list(map(int, r)), b)) for b in W1]
out["greedy_doubled"] = [sorted(map(lambda r: list(map(int, r)), b)) for b in W2]
for mult in (1, 2):
    o = M.lp_bound(sim, mult, integer=True, time_limit=120)
    out[f"ilp_{mult}"] = {"objective": o.get("objective"), "status": o["message"],
                          "rows": sorted([list(map(int, r)) for r in o.get("rows", [])])}
os.makedirs(os.path.join(HERE, "analysis"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "analysis", f"simcost_{tag}.json"), "w"), indent=0, default=float)
print(tag, "done")
