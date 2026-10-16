#!/usr/bin/env python3
"""Claim C18 test (gpu_design.json, reach claim C18): rerun the P3 party-regime
covering (p3_prework/covering/covering.py) and the SiGeC cost-aware covering
(p3_limits/cost_covering.py via cost_models.py) with the MACE-MD per-point
cost 246 min (MACE-MP-0 small, GB10 + cuEquivariance) replaced by the cost of
MACE-MPA-0 medium, and report whether any batch choice changes. Code runs
unchanged except the cost constant and the output paths.
Usage: python rerun_cost_mpa.py <cost_min> <tag>"""
import json, os, sys, runpy, types
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
cost, tag = float(sys.argv[1]), sys.argv[2]
out = os.path.join(HERE, "analysis", "cost_" + tag); os.makedirs(out, exist_ok=True)

# 1. party-regime covering
f = os.path.join(MT, "p3_prework", "covering", "covering.py")
src = open(f).read()
for a, b in [('"MACE-MD": 246.0,', '"MACE-MD": %r,' % cost), ('"MACE-MD": 3 * 246.0,', '"MACE-MD": 3 * %r,' % cost),
             ('os.path.join(HERE, "results.json")', 'os.path.join(__OUT__, "covering_results.json")'),
             ('os.path.join(HERE, "covering_grid.png")', 'os.path.join(__OUT__, "covering_grid.png")')]:
    assert src.count(a) == 1, a; src = src.replace(a, b)
sys.path.insert(0, os.path.dirname(f))
exec(compile(src, f + " [cost swap]", "exec"), {"__file__": f, "__name__": "__main__", "__OUT__": out})
