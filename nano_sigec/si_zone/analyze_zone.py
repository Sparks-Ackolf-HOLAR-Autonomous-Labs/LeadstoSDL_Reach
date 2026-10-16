#!/usr/bin/env python3
"""Analysis of the Si-depleted zone check (zone_design.json, ledger seq 62).

Written and committed before any Z1 or Z2 output existed. Run only after
commit_zone.py has ledgered chpc/out/ and md/results/. Refuses to run if
zone_design.json changed after registration. Applies the gates, the four
predictions and the Z3 decision rule as registered; choices the design
leaves open are listed under "analysis_time_choices". Output: zone_results.json.
The ledger entry for the decision is made by a separate apply step."""
import hashlib, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, "zone_design.json")
reg = open(os.path.join(HERE, "PREREGISTERED_SHA256")).read().split()[0]
if hashlib.sha256(open(DESIGN, "rb").read()).hexdigest() != reg:
    sys.exit("zone_design.json changed after registration")
D = json.load(open(DESIGN))
KB = 8.617333262e-5  # eV/K
RP = 5.0             # MACE particle radius, A (chpc/mace_zone.py)
C_PARENT = D["posthoc_basis_disclosed"]["c_fit"]
CHOICES = [
    "Z1 profile: p(d) = 1 - exp(-dE(d)/kT) at the mean site distance of each bin; linear between bin centres; "
    "p held at the innermost-bin value from the interface (5 A) inward to the first bin; after the last significant "
    "bin p falls linearly to zero at the next bin centre and stays zero",
    "Z1 w_eq solves (RP + w)^3 - RP^3 = 3 * integral of p(r) r^2 dr; a negative integral (Ge enrichment) gives w_eq = 0",
    "Z2 pocket fraction taken over the 7 fitted bins per half from the equilibrated box, as in the parent fit",
]


def mg(f, c):
    return (c + 2 + 2 * f * (c - 1)) / (c + 2 - f * (c - 1))


out = {"design_sha256": reg, "analysis_time_choices": CHOICES}

# ---------------- Z1
Z1 = os.path.join(HERE, "chpc", "out")
ref = json.load(open(os.path.join(Z1, "ref.json")))
rows = [json.load(open(os.path.join(Z1, f))) for f in sorted(os.listdir(Z1))
        if f.endswith(".json") and f != "ref.json"]
g1 = {r["task"]: r["gate_pass"] for r in rows}
g1["ref"] = ref["gate_pass"]
out["G1"] = {"per_task": g1, "pass": all(g1.values())}
far = [r["E_eV"] for r in rows if r["task"].startswith("far_")]
e_far = float(np.mean(far))
noise_far = abs(far[0] - far[1]) / 2
bins = {}
for r in rows:
    if r["task"].startswith("d"):
        b = float(r["task"][1:].split("_")[0])
        bins.setdefault(b, []).append((r["d_A"], r["E_eV"] - e_far))
prof = []
for b in sorted(bins):
    d = float(np.mean([v[0] for v in bins[b]]))
    de = [v[1] for v in bins[b]]
    m, hr = float(np.mean(de)), (max(de) - min(de)) / 2
    floor = max(noise_far, hr, 0.01)
    prof.append({"bin": b, "d_A": d, "dE_eV": de, "dE_mean": m, "half_range": hr,
                 "significant": abs(m) >= floor})
out["Z1"] = {"E_far_eV": e_far, "far_half_diff_eV": noise_far, "profile": prof}
last = max([i for i, p in enumerate(prof) if p["significant"]], default=-1)


def w_eq(T):
    if last < 0:
        return 0.0, 0.0
    ds = [RP] + [p["d_A"] for p in prof[:last + 1]]
    ps = [1 - math.exp(-prof[0]["dE_mean"] / (KB * T))]
    ps += [1 - math.exp(-p["dE_mean"] / (KB * T)) if p["significant"] else 0.0 for p in prof[:last + 1]]
    if last + 1 < len(prof):
        ds.append(prof[last + 1]["d_A"]); ps.append(0.0)
    r = np.linspace(RP, ds[-1], 4001)
    pr = np.interp(r, ds, ps)
    integ = float(np.trapezoid(pr * r ** 2, r))
    if integ <= 0:
        return 0.0, integ
    return (RP ** 3 + 3 * integ) ** (1 / 3) - RP, integ


W = {}
for T in (1373, 1473):
    w, integ = w_eq(T)
    W[T] = w
    out["Z1"][f"w_eq_A_{T}K"] = w
    out["Z1"][f"integral_{T}K"] = integ
out["PrZ1"] = {"dE_innermost_eV": prof[0]["dE_mean"], "pass": prof[0]["dE_mean"] > 0}
out["PrZ4"] = {"w_eq_1473K_A": W[1473], "pass": W[1473] < 7.0}

# ---------------- Z2
RES = os.path.join(HERE, "md", "results")
runs = {}
for l in open(os.path.join(HERE, "md", "points.txt")):
    if not l.strip():
        continue
    tag, R, w, sh, sic, seed = l.split()
    base = os.path.join(RES, f"{tag}_s{seed}")
    j = json.load(open(base + ".json"))
    kv = {}
    for line in open(base + ".log"):
        p = line.split()
        if p and p[0] in ("SIC_G1_START", "SIC_G1_END", "MPT_BOX"):
            kv[p[0]] = [float(v) for v in p[1:]]
    runs.setdefault(tag, []).append({"seed": int(seed), "kappa": j["kappa_W_mK"], "box": kv["MPT_BOX"],
                                     "R": float(R), "w": float(w), "g1s": kv.get("SIC_G1_START"),
                                     "g1e": kv.get("SIC_G1_END")})
host = [r["kappa"] for r in runs["host"]]
kh = float(np.mean(host))
out["G3"] = {"host": host, "rel_diff": abs(host[0] - host[1]) / kh, "pass": abs(host[0] - host[1]) / kh <= 0.08}
gaps = {f"s{r['seed']}": [r["g1s"][0] - r["g1s"][1], r["g1e"][0] - r["g1e"][1]] for r in runs["p10w12"]}
out["G2"] = {"gaps_A": gaps, "pass": all(min(v) >= 5.7 for v in gaps.values())
             and all(r["kappa"] > 0 and np.isfinite(r["kappa"]) for rr in runs.values() for r in rr)}


def ratio(tag):
    v = [r["kappa"] / kh for r in runs[tag]]
    return float(np.mean(v)), (max(v) - min(v)) / 2


def f_fit(R, w, box):
    return 4 / 3 * math.pi * (R + w) ** 3 / (box[0] * box[1] * 7 * box[2] / 20)


pz2 = {}
for tag in ("sh10w7", "sh10w12"):
    m, hr = ratio(tag)
    pred = D["predictions"]["PrZ2"][tag]["kappa_over_host"]
    ff = float(np.mean([f_fit(r["R"], r["w"], r["box"]) for r in runs[tag]]))
    pz2[tag] = {"obs": m, "half_range": hr, "pred": pred, "f_fit": ff, "pass": abs(m - pred) <= max(0.05, hr)}
out["PrZ2"] = {"rows": pz2, "pass": all(v["pass"] for v in pz2.values())}
m3, hr3 = ratio("p10w12")
out["PrZ3"] = {"obs": m3, "half_range": hr3, "pred": D["predictions"]["PrZ3"]["p10w12"]["kappa_over_host"],
               "pass": m3 > 1}

c_use, c_note = C_PARENT, "parent post-hoc fit (PrZ2 passed)"
if not out["PrZ2"]["pass"]:
    par = json.load(open(os.path.join(HERE, "..", "small_sic", "md_results.json")))["runs"]
    hp = np.mean([par[k]["kappa"] for k in par if k.startswith("host")])
    pts = []
    for R in (10, 15, 20):
        sh = [par[k] for k in par if k.startswith(f"sh{R}_")]
        pts.append((np.mean([f_fit(R, 7, s["box"]) for s in sh]), np.mean([s["kappa"] for s in sh]) / hp))
    for tag in ("sh10w7", "sh10w12"):
        pts.append((pz2[tag]["f_fit"], pz2[tag]["obs"]))
    cs = np.exp(np.linspace(0, 6, 6001))
    loss = [sum((math.log(mg(f, c)) - math.log(k)) ** 2 for f, k in pts) for c in cs]
    c_use, c_note = float(cs[int(np.argmin(loss))]), "refit on five geometries (PrZ2 failed; registered z2_fallback)"
out["c_used"] = {"c": c_use, "note": c_note}

# ---------------- Z3
z3 = D["stages"]["Z3"]
phi = z3["phi_SiC_at_1at_C"]
r_part = {25.0: 0.125, 50.0: 0.147}  # density edge, ledger seq 61 (decision_robustness.json)
w_use = W[1473] if out["G1"]["pass"] else 7.0
out["Z3"] = {"w_used_A": w_use, "w_source": "Z1 at 1473 K" if out["G1"]["pass"] else "z1_fallback: parent 7 A", "rows": {}}
for R, rp in r_part.items():
    row = {}
    for lab, w in (("1473K", W[1473]), ("1373K", W[1373]), ("used", w_use)):
        fp = phi * ((R + w) ** 3 - R ** 3) / R ** 3
        g = mg(fp, c_use)
        row[lab] = {"w_A": w, "f_pocket": fp, "pocket_factor": g, "cancel": (g - 1) / rp,
                    "net_reduction": 1 - (1 - rp) * g}
    # zone width at which the pocket cancels the particle entirely
    lo, hi = 0.0, R * ((1 + 0.5 / phi) ** (1 / 3) - 1)  # keep f_pocket <= 0.5 so MG stays physical
    for _ in range(80):
        mid = (lo + hi) / 2
        g = mg(phi * ((R + mid) ** 3 - R ** 3) / R ** 3, c_use)
        lo, hi = (mid, hi) if (g - 1) / rp < 1 else (lo, mid)
    row["w_star_A"] = (lo + hi) / 2
    out["Z3"]["rows"][f"R{R/10:g}nm"] = row
cancels = [v["used"]["cancel"] for v in out["Z3"]["rows"].values()]
if all(c < 0.2 for c in cancels):
    branch = "strengthen"
elif all(c < 1 for c in cancels):
    branch = "correct"
else:
    branch = "downweight"
out["decision"] = {"branch": branch, "cancel": cancels, "rule": D["decision_rule"][branch]}
json.dump(out, open(os.path.join(HERE, "zone_results.json"), "w"), indent=1)
print(json.dumps({"w_eq": W, "PrZ1": out["PrZ1"]["pass"], "PrZ2": out["PrZ2"]["pass"], "PrZ3": out["PrZ3"]["pass"],
                  "PrZ4": out["PrZ4"]["pass"], "gates": [out["G1"]["pass"], out["G2"]["pass"], out["G3"]["pass"]],
                  "branch": branch, "cancel": cancels}, indent=1))
