#!/usr/bin/env python3
"""P5 revision event 1, prediction stage (no compute): the reach of a change
of MACE foundation-potential version, predicted from the campaign record only.

Event: every MACE calculation of the campaign (MACE-MP-0 medium float64 for
the where-carbon-goes and Si-zone relaxations; MACE-MP-0 small float32 for
the party-4b and P3 molecular dynamics) is to be repeated with a newer
foundation model trained on more data (for example MACE-MPA-0 or
MACE-OMAT-0).

What the script does (python3 standard library only, seconds of CPU):
  1. builds a dependency graph over the ledger (phase_c/ledger_campaign.jsonl)
     with every edge labelled by link type:
       commits_output  MACE output files -> the ledger entry committing them
       explicit_field  payload key ending _seq/_seqs, or rests_on (int or
                       numeric string)
       explicit_opid   payload string naming an earlier op_id
       text_citation   free-text "ledger seq N", "seq N", "ledger N", ranges
       file_path       the entry names a file in a directory whose code reads
                       a MACE result (directly, through analyze_sigec, or via
                       a hand-copied MACE constant)
       same_campaign   earlier entry of the same campaign (as P4 T0 replay)
       parent_campaign payload parent_campaign naming an earlier campaign
  2. seeds it with the MACE computations found on disk (model string checked
     in every raw output file) and propagates forward in campaign time;
  3. reports the reach under four link tiers (explicit only, plus prose
     citations, plus file paths, plus campaign names);
  4. extends the reach to figure scripts and to paper-draft lines;
  5. classifies each reached claim (decision may flip / magnitude only /
     unaffected) from margins read out of the committed result files;
  6. picks the smallest set of MACE recomputations that settles every
     'decision may flip' item, costed from recorded wall times.
Output: p5_reach/reach_prediction.json."""
import glob
import itertools
import json
import math
import os
import re
from collections import defaultdict, deque

HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.dirname(HERE)
LEDGER = os.path.join(MT, "phase_c", "ledger_campaign.jsonl")
OUT = os.path.join(HERE, "reach_prediction.json")

# plausible size of a version change, taken from the record: the registered
# O3 categories (ledger 122-123, ai_theorist/theorist_brief.md) put the
# boundary between "magnitude within" and "magnitude changes" at 0.3 eV
SHIFT_EV = 0.3
TIERS = [
    ("T0_explicit", {"commits_output", "explicit_field", "explicit_opid"}),
    ("T1_plus_prose_citations", {"commits_output", "explicit_field", "explicit_opid", "text_citation"}),
    ("T2_plus_file_paths", {"commits_output", "explicit_field", "explicit_opid", "text_citation", "file_path"}),
    ("T3_plus_campaign_names", {"commits_output", "explicit_field", "explicit_opid", "text_citation", "file_path",
                                "same_campaign", "parent_campaign"}),
]


def rel(p):
    return os.path.relpath(p, MT)


def load_json(p):
    with open(os.path.join(MT, p)) as f:
        return json.load(f)


# ---------------------------------------------------------------- ledger
E = [json.loads(l) for l in open(LEDGER)]
SEQ = {e["seq"]: e for e in E}


def campaign_of(p):
    return p.get("campaign") or p.get("action") or (p.get("op_id") or "unnamed").rsplit("-20", 1)[0]


CAMP = {e["seq"]: campaign_of(e["payload"]) for e in E}
OPID = {e["payload"].get("op_id"): e["seq"] for e in E if e["payload"].get("op_id")}


def strings(obj, key=None):
    """(key, string) pairs, skipping hashes and roots."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "sha256" in k or "merkle" in k or k in ("entry_hash", "row_ids"):
                continue
            yield from strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v, key)
    elif isinstance(obj, str):
        yield key, obj


def explicit_fields(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("_seq") or k.endswith("_seqs") or k == "rests_on":
                for x in (v if isinstance(v, list) else [v]):
                    if isinstance(x, int):
                        out.add(x)
                    elif isinstance(x, str) and x.strip().isdigit():
                        out.add(int(x))
            else:
                explicit_fields(v, out)
    elif isinstance(obj, list):
        for v in obj:
            explicit_fields(v, out)
    return out


CIT = re.compile(r"\b(?:ledger(?:\s+(?:seq|entry|entries))?|seq|entry|entries)\s+(\d{1,3})"
                 r"(?:\s*(?:-|to|and|,)\s*(\d{1,3}))?", re.I)


def text_citations(payload):
    out = set()
    for k, s in strings(payload):
        for m in CIT.finditer(s):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            if b < a or b - a > 10:
                b = a
            out.update(range(a, b + 1))
    return out


PATH = re.compile(r"[A-Za-z0-9_./~-]*[A-Za-z0-9_-]/[A-Za-z0-9_.-]+\.(?:json|py|md|txt|csv)")


def paths_of(payload):
    s = json.dumps(payload)
    return sorted(set(PATH.findall(s)))


# ---------------------------------------------------------------- MACE seeds
SEEDS = [
    {"id": "MACE_P4B", "what": "party 4b: MACE-MD Muller-Plathe kappa, 2 points (x = 0.15, 0.5; 300 K)",
     "raw_glob": "party4_mace/raw/*.json", "model_key": "engine", "wall_key": "wall_s",
     "ledger_seq": 1, "wall_unit": "GPU-h (DGX GB10)"},
    {"id": "MACE_M1", "what": "where-carbon-goes gate M1: 57 cell+position relaxations (216-site cells)",
     "raw_glob": "nano_sigec/m1/out/*.json", "model_key": "model", "wall_key": "wall_s",
     "ledger_seq": 47, "wall_unit": "CPU-task-h (CHPC notchpeak-guest, 16 cores)"},
    {"id": "MACE_M1C", "what": "where-carbon-goes converged rerun M1c: 51 relaxations",
     "raw_glob": "nano_sigec/m1c/out/*.json", "model_key": "model", "wall_key": "wall_s",
     "ledger_seq": 54, "wall_unit": "CPU-task-h (CHPC notchpeak-guest, 16 cores)"},
    {"id": "MACE_Z1", "what": "Si-zone stage Z1: Ge segregation energy around an embedded SiC sphere, 19 relaxations",
     "raw_glob": "nano_sigec/si_zone/chpc/out/*.json", "model_key": "model", "wall_key": "wall_s",
     "ledger_seq": 69, "wall_unit": "CPU-task-h (CHPC notchpeak-guest, 16 cores)"},
    {"id": "MACE_P3", "what": "P3 hidden-subset MACE-MD: 89 rNEMD runs (71 planner points, 16 hidden, 2 repeats)",
     "raw_glob": "p3_mace/raw/out/*.json", "model_key": "engine", "wall_key": "wall_s_this_attempt",
     "ledger_seq": 72, "wall_unit": "GPU-h (CHPC guest GPUs, mixed)"},
    {"id": "MACE_P4T1", "what": "P4 stage T1 (in progress): MACE-MP-0 medium float32 MD of Ge0.88Sn0.12 with "
     "vacancies; only the two benchmark files are in the repository so far",
     "raw_glob": "p4_tskg/T1_md/bench/*.json", "model_key": "args.model", "wall_key": "eq_s",
     "ledger_seq": 126, "wall_unit": "GPU-h (CHPC guest GPU, benchmark only)"},
]


def dig(d, key):
    for k in key.split("."):
        d = d.get(k) if isinstance(d, dict) else None
    return d


for s in SEEDS:
    fs = sorted(glob.glob(os.path.join(MT, s["raw_glob"])))
    models, wall = defaultdict(int), 0.0
    for f in fs:
        d = json.load(open(f))
        m = str(dig(d, s["model_key"]))
        models[m if "mace" in m.lower() else f"MACE-MP-0 {m} (from args; mace_mp)"] += 1
        wall += float(dig(d, s["wall_key"]) or 0.0)
    s["n_files"] = len(fs)
    s["models_in_files"] = dict(models)
    s["model_check_all_mace"] = bool(fs) and all("mace" in m.lower() for m in models)
    s["recorded_wall_h"] = round(wall / 3600.0, 2)
    s["ledger_campaign"] = CAMP[s["ledger_seq"]]
    s["ledger_op_id"] = SEQ[s["ledger_seq"]]["payload"].get("op_id")
# MACE numbers present in code as constants, with no ledger entry of their own
CONST_SEED = {"id": "MACE_CONST", "what": "MACE-derived constants copied into code (no ledger entry): "
              "P08 fault magnitude 0.50-0.60 x Tersoff, detector-v2 MACE/Tersoff lattice ratio, "
              "MACE-MD cost 246 in the P3 covering cost model, 4.1 h per point in p3_limits",
              "ledger_seq": None}

# ---------------------------------------------------------------- code scan: which directories read MACE output
TOKENS = [  # (regex, seeds it attributes to)
    (r"party4_mace|[\"']MACE-MD[\"']", ["MACE_P4B"]),
    (r"\bm1_summary", ["MACE_M1"]),
    (r"m1c_summary|SIGEC_M1_SUMMARY|analyze_sigec", ["MACE_M1C"]),
    (r"zone_results|mace_zone", ["MACE_Z1"]),
    (r"p3_mace", ["MACE_P3"]),
    (r"A_MACE|_ratio_mace|mace_over_tersoff|COST_BASE|cost_models", ["MACE_CONST"]),
]
SKIP_DIRS = ("paper_repos", ".git", "asta_search_results", "p5_reach", "__pycache__")
dir_seeds = defaultdict(lambda: defaultdict(set))  # dir -> seed -> {script}
fig_scripts = defaultdict(set)  # script -> seeds
for root, dirs, files in os.walk(MT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        try:
            txt = open(p, errors="ignore").read()
        except OSError:
            continue
        if "mace" not in txt.lower():
            continue
        hit = set()
        for rx, sids in TOKENS:
            if re.search(rx, txt):
                hit.update(sids)
        if "COST_BASE" in txt and "MACE" not in txt:
            hit.discard("MACE_CONST")
        for sid in hit:
            dir_seeds[rel(root)][sid].add(fn)
        if rel(root).startswith("papers") and hit:
            fig_scripts[rel(p)] = hit


DATA_SUBDIRS = {"results", "out", "raw", "md", "chpc", "bench", "logs", "m1", "m1c"}


def mace_dir_for(path):
    """Directory holding MACE-reading code: the file's own directory, or its
    parent when the file sits in a data subfolder (results/, out/, raw/ ...)."""
    d = os.path.dirname(path)
    for _ in range(3):
        if d in dir_seeds:
            return d
        if os.path.basename(d) not in DATA_SUBDIRS:
            return None
        d = os.path.dirname(d)
    return None


# ---------------------------------------------------------------- edges
edges = []  # (src, dst, type, evidence)
for s in SEEDS:
    edges.append((f"M:{s['id']}", f"L:{s['ledger_seq']}", "commits_output",
                  f"{s['n_files']} files {s['raw_glob']} committed at ledger {s['ledger_seq']}"))
camp_entries = defaultdict(list)
design_dirs = defaultdict(set)
for e in E:
    p = e["payload"]
    if p.get("design_file"):
        design_dirs[CAMP[e["seq"]]].add(os.path.dirname(p["design_file"]))
unresolved_parents = []
link_counts = defaultdict(int)
for e in E:
    s, p = e["seq"], e["payload"]
    ex = {x for x in explicit_fields(p, set()) if x < s}
    for x in sorted(ex):
        edges.append((f"L:{x}", f"L:{s}", "explicit_field", "payload seq field"))
    op = set()
    for k, txt in strings(p):
        if k in ("op_id", "campaign", "action"):
            continue
        for oid, oseq in OPID.items():
            if oseq < s and len(oid) >= 15 and oid in txt and oseq not in ex:
                op.add(oseq)
    for x in sorted(op):
        edges.append((f"L:{x}", f"L:{s}", "explicit_opid", "payload names op_id " + SEQ[x]["payload"]["op_id"]))
    tc = {x for x in text_citations(p) if x < s and x in SEQ} - ex - op
    for x in sorted(tc):
        edges.append((f"L:{x}", f"L:{s}", "text_citation", "free-text ledger citation"))
    # file paths
    bases = [""] + sorted(design_dirs.get(CAMP[s], []))
    for path in paths_of(p):
        path = path.lstrip("./")
        cands = [os.path.normpath(os.path.join(b, path)) for b in bases]
        real = [c for c in cands if os.path.exists(os.path.join(MT, c))] or cands[:1]
        md = None
        for c in real:
            md = mace_dir_for(c)
            if md:
                path = c
                break
        if not md:
            continue
        for sid, scripts in dir_seeds[md].items():
            src_seq = next((x["ledger_seq"] for x in SEEDS if x["id"] == sid), None)
            if src_seq is not None and src_seq >= s:
                continue  # dependency must precede the entry in campaign time
            edges.append((f"M:{sid}", f"L:{s}", "file_path",
                          f"{path} sits with {md}/{{{', '.join(sorted(scripts))}}} which read {sid}"))
    # same campaign
    for x in camp_entries[CAMP[s]]:
        edges.append((f"L:{x}", f"L:{s}", "same_campaign", CAMP[s]))
    camp_entries[CAMP[s]].append(s)
    # parent campaign by name
    pc = p.get("parent_campaign")
    if pc:
        name = pc.split(" (")[0].strip()
        hits = [c for c in camp_entries if c == name or c.startswith(name) or name.startswith(c)]
        if not hits:
            unresolved_parents.append({"seq": s, "parent_campaign": pc})
        for c in hits:
            for x in camp_entries[c]:
                if x < s:
                    edges.append((f"L:{x}", f"L:{s}", "parent_campaign", pc))
# figure scripts (paper figures) read MACE outputs directly
for fp, sids in sorted(fig_scripts.items()):
    for sid in sorted(sids):
        edges.append((f"M:{sid}", f"FIG:{fp}", "file_path", "figure script reads " + sid))
# de-duplicate, keep the strongest label per pair
RANK = {"commits_output": 0, "explicit_field": 1, "explicit_opid": 2, "text_citation": 3, "file_path": 4,
        "same_campaign": 5, "parent_campaign": 6}
best = {}
for a, b, t, ev in edges:
    k = (a, b)
    if k not in best or RANK[t] < RANK[best[k][0]]:
        best[k] = (t, ev)
ADJ = defaultdict(list)
for (a, b), (t, ev) in best.items():
    ADJ[a].append((b, t, ev))
    link_counts[t] += 1

SEED_NODES = [f"M:{s['id']}" for s in SEEDS] + ["M:MACE_CONST"]


def reach(allowed):
    prev = {n: None for n in SEED_NODES}
    q = deque(SEED_NODES)
    while q:
        u = q.popleft()
        for v, t, ev in ADJ.get(u, []):
            if t in allowed and v not in prev:
                prev[v] = (u, t, ev)
                q.append(v)
    return prev


def path_to(prev, v):
    out = []
    while prev.get(v):
        u, t, ev = prev[v]
        out.append({"from": u, "to": v, "link": t, "evidence": ev})
        v = u
    return list(reversed(out))


tier_reach = {name: reach(allowed) for name, allowed in TIERS}
full = tier_reach["T3_plus_campaign_names"]


def entries(prev):
    return sorted(int(n[2:]) for n in prev if n.startswith("L:"))


first_tier = {}
for name, _ in TIERS:
    for n in tier_reach[name]:
        first_tier.setdefault(n, name)

# ---------------------------------------------------------------- paper statements
DRAFTS = {"P1": "papers/paper1_j_mater_chem_a", "P2": "papers/paper2_adv_intell_discov",
          "P3": "papers/paper3_mol_syst_des_eng"}
LCIT = re.compile(r"(?:ledger|entr(?:y|ies)|seq)\D{0,12}?(\d{1,3})(?:\s*(?:--|-|to|and|,)\s*(\d{1,3}))?", re.I)
paper_lines = []
for paper, d in DRAFTS.items():
    for fn in ("draft.tex", "esi_body.tex", "annex_ledger_table.tex"):
        p = os.path.join(MT, d, fn)
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p, errors="ignore"), 1):
            if line.lstrip().startswith("%"):
                continue
            kw = bool(re.search(r"MACE", line))
            cites = set()
            for m in LCIT.finditer(line):
                a = int(m.group(1))
                b = int(m.group(2)) if m.group(2) else a
                cites.update(range(a, (b if a <= b <= a + 10 else a) + 1))
            hit = {c for c in cites if f"L:{c}" in full}
            if kw or hit:
                paper_lines.append({"paper": paper, "file": f"{d}/{fn}", "line": i,
                                    "link": "keyword_MACE" if kw else "ledger_citation",
                                    "cites_reached_entries": sorted(hit),
                                    "first_tier_of_cited": sorted({first_tier[f'L:{c}'] for c in hit}),
                                    "text": line.strip()[:200]})

# ---------------------------------------------------------------- margins from the record
m1c = load_json("nano_sigec/m1c/m1c_summary.json")
zone = load_json("nano_sigec/si_zone/zone_results.json")
zdes = load_json("nano_sigec/si_zone/zone_design.json")
p3r = load_json("p3_mace/results/p3_mace_results.json")
h2h = load_json("phase_c/head_to_head/h2h_results.json")
sig = load_json("nano_sigec/results/sigec_results_m1c.json")

dprec = {x: v["dE_prec_mean_eV"] for x, v in m1c["per_x"].items()}
dsite = {x: v["dE_site_mean_eV"] for x, v in m1c["per_x"].items() if v["dE_site_mean_eV"] is not None}
lat = {k: v["rel"] for k, v in m1c["M1a"]["rows"].items()}
noise = min(p3r["noise_floor_abs_log_diff"])
sc = p3r["scores"]
imp = p3r["materials"]["importance"]


# Z1: smallest uniform repulsive shift of the Ge-SiC profile that would flip the zone decision
KB, RP = 8.617333262e-5, 5.0
prof = zone["Z1"]["profile"]
phi = zdes["stages"]["Z3"]["phi_SiC_at_1at_C"]
c_mg = zone["c_used"]["c"]
r_part = {25.0: 0.125, 50.0: 0.147}


def mg(f, c):
    return (c + 2 + 2 * f * (c - 1)) / (c + 2 - f * (c - 1))


def w_eq(shift, T=1473.0, near_only=None):
    """shift: uniform eV added to every bin, or (if near_only is a distance in A)
    only to bins closer than near_only."""
    de = [p["dE_mean"] + (shift if near_only is None or p["d_A"] < near_only else 0.0) for p in prof]
    hr = [p["half_range"] for p in prof]
    sigf = [abs(v) >= max(h, 0.01) for v, h in zip(de, hr)]
    last = max([i for i, s in enumerate(sigf) if s], default=-1)
    if last < 0:
        return 0.0
    ds = [RP] + [p["d_A"] for p in prof[:last + 1]]
    ps = [1 - math.exp(-de[0] / (KB * T))] + [1 - math.exp(-de[i] / (KB * T)) if sigf[i] else 0.0
                                              for i in range(last + 1)]
    if last + 1 < len(prof):
        ds.append(prof[last + 1]["d_A"])
        ps.append(0.0)
    n = 4000
    integ = 0.0
    for k in range(n):
        r0 = RP + (ds[-1] - RP) * k / n
        r1 = RP + (ds[-1] - RP) * (k + 1) / n
        def interp(r):
            for j in range(len(ds) - 1):
                if ds[j] <= r <= ds[j + 1]:
                    t = (r - ds[j]) / (ds[j + 1] - ds[j]) if ds[j + 1] > ds[j] else 0.0
                    return ps[j] + t * (ps[j + 1] - ps[j])
            return ps[-1]
        integ += 0.5 * (interp(r0) * r0 ** 2 + interp(r1) * r1 ** 2) * (r1 - r0)
    if integ <= 0:
        return 0.0
    return (RP ** 3 + 3 * integ) ** (1 / 3) - RP


def cancels(shift, near_only=None):
    w = w_eq(shift, near_only=near_only)
    return {R: (mg(phi * ((R + w) ** 3 - R ** 3) / R ** 3, c_mg) - 1) / rp for R, rp in r_part.items()}, w


base_cancel, base_w = cancels(0.0)
lo, hi = 0.0, 2.0
if max(cancels(hi)[0].values()) >= 0.2:
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if max(cancels(mid)[0].values()) < 0.2 else (lo, mid)
    zone_flip_shift = round(hi, 3)
else:
    zone_flip_shift = None
zone_flip_w = round(cancels(zone_flip_shift)[1], 2) if zone_flip_shift else None
# shift confined to the two bins that carry signal (6.5 and 7.5 A): the largest zone it can make
near_cut = 8.0
near_max_cancel, near_max_w = cancels(5.0, near_only=near_cut)
near_max_cancel = {str(k): round(v, 3) for k, v in near_max_cancel.items()}

mf_rows = {k: v for k, v in h2h["methods"].items() if "MF" in k.upper() or "GP" in k.upper()}
mf_picks = {k: v.get("M3_argmin_1100K") for k, v in mf_rows.items()}
grid = h2h["truth"]["kappa_1100K_grid"]
kmin = min(grid.values())
flat = sorted(float(x) for x, v in grid.items() if v <= 1.08 * kmin)

# ---------------------------------------------------------------- claims and their predicted sensitivity
C = []


def claim(cid, seqs, papers, statement, cls, reason, predicted, refuted_if, settle, numbers=None):
    C.append({"id": cid, "ledger_seqs": seqs, "papers": papers, "statement": statement,
              "predicted_class": cls, "reason_from_record": reason, "predicted_outcome": predicted,
              "refuted_if": refuted_if, "settled_by": settle, "numbers": numbers or {}})


FLIP, MAG, UNA = "decision may flip", "magnitude only", "unaffected"
claim("C1_lattice_gate", [53, 54, 55], ["P1", "P2"],
      "gate M1c-c (and M1a): bulk lattice constants of Si, Ge, 3C-SiC within 2.5% of experiment; passing it "
      "is what lifted the 'unvalidated' flag on the where-carbon-goes energies (strengthen, ledger 55)",
      FLIP, f"Ge sits at +{lat['Ge']*100:.2f}% against a 2.5% gate (margin {2.5-lat['Ge']*100:.2f} percentage "
      "points). Newer foundation models are still fitted to PBE-family data, and PBE itself overestimates the "
      "Ge lattice constant by about 2%, so a shift of half a percentage point is within a version change.",
      "gate passes again (Ge between +1.5% and +2.5%); P(fail) about 0.3",
      "Ge lattice constant from the new model more than 2.5% above 5.658 A (gate fails, the strengthen of "
      "ledger 55 reverts to 'unvalidated'); for the passing prediction, also refuted if Ge falls below +1.5%",
      ["R_M1C"], {"rel_lattice_error": lat, "gate": 0.025})
claim("C2_carbon_leaves_lattice", [47, 49, 54, 55], ["P1", "P2", "P3"],
      "carbon on lattice sites gains energy by leaving to form SiC (dE_prec < -0.5 eV per C at x = 0, 0.2, 0.5): "
      "P1 'Carbon leaves the lattice', prediction PrC2 (sign part)",
      MAG, f"dE_prec = {', '.join(f'{v:.2f}' for v in dprec.values())} eV at x = {', '.join(dprec)}; margin to the "
      f"registered -0.5 eV threshold {min(-v for v in dprec.values())-0.5:.2f} eV and to the sign "
      f"{min(-v for v in dprec.values()):.2f} eV, against a plausible version shift of {SHIFT_EV} eV",
      "sign and threshold hold at every x; values move by 0.05-0.3 eV",
      "dE_prec above -0.5 eV at any x (PrC2 verdict flips) or above 0 eV (carbon would stay on lattice sites)",
      ["R_M1C"], {"dE_prec_eV": dprec})
claim("C3_carbon_trend_with_Ge", [49, 55], ["P1"],
      "PrC2 trend part: carbon precipitation is more favourable at x = 0.5 than at x = 0",
      FLIP, f"difference dE_prec(0.5) - dE_prec(0) = {dprec['0.5']-dprec['0']:.2f} eV, below the {SHIFT_EV} eV "
      "plausible shift; Ge-rich and Ge-free cells need not shift together",
      "trend holds (x = 0.5 more negative than x = 0 by 0.1-0.4 eV)",
      "dE_prec(0.5) >= dE_prec(0) under the new model",
      ["R_M1C"], {"difference_eV": dprec["0.5"] - dprec["0"]})
claim("C4_carbon_prefers_Si_rich_shells", [49, 55, 58, 62], ["P1"],
      "PrC2b: substitutional C prefers Si-rich neighbour shells (dE_site > 0 at x = 0.2, 0.5); this motivated the "
      "Si-rich pocket imposed around SiC particles in the small-SiC MD design (ledger 58)",
      FLIP, f"dE_site = {', '.join(f'{v:.2f}' for v in dsite.values())} eV at x = {', '.join(dsite)}; the x = 0.2 "
      f"margin ({min(dsite.values()):.2f} eV) is inside the {SHIFT_EV} eV band",
      "sign holds at both x (values 0.1-0.4 eV)",
      "dE_site <= 0 at x = 0.2 or 0.5",
      ["R_M1C"], {"dE_site_eV": dsite})
claim("C5_size_misfit_delta_C", [48, 49, 55, 57, 76], ["P1", "P3"],
      "substitutional size misfit delta_C (PrC1) and the substitutional strain upper bound it feeds",
      MAG, "MACE delta_C lies within 6% of the modified-Vegard fallback that the design already carries; replacing "
      "it moved the strain upper bound by 1.4% (2.533 -> 2.497 W/mK, ledger 55); PrC3 records that SiC at "
      "R = 2.5 nm beats substitutional C even at eps = 39, so no pick reads delta_C",
      "delta_C within 10% of -0.394; every pick unchanged",
      "delta_C outside +/-30% of modified Vegard (PrC1 fails) or any screening pick changes",
      ["R_M1C"], {"delta_C": {x: v["delta_C"] for x, v in m1c["per_x"].items()}})
claim("C6_screening_pick", [55, 61, 77, 80, 105, 110], ["P1", "P3"],
      "recipe pick x = 0.3, 3 at% C as few-nm SiC (equilibrium-constrained and unconstrained picks)",
      MAG, "the equilibrium constraint reads only the sign of dE_prec (margin 1.44 eV); the unconstrained pick is "
      "already a SiC form (PrC3), so even a sign change would not move it; the contrast sweep "
      "(small_sic/decision_robustness.json) kept x = 0.3, 3 at% C across the whole lam2 range; the radius "
      "correction (ledger 105, 110) rests on Tersoff particle MD, not on MACE",
      "pick unchanged (x = 0.3, 3 at% C, few-nm SiC)",
      "any change of x, carbon content or carbon form in the pick after rerunning analyze_sigec on the new summary",
      ["R_M1C"])
claim("C7_ge_saving", [61, 70, 105, 110], ["P1"],
      "Ge saving at equal kappa (13.7-16.2% at R = 2.5 nm after ledger 105/110)",
      UNA, "computed from Tersoff particle MD and almaBTE modes with SiC forms; no MACE quantity enters the SiC "
      "scattering term; reached only through shared model code (analyze_sigec loads the MACE summary)",
      "numbers identical to the last digit after rerunning the analysis on the new MACE summary",
      "any change in the ledger-110 saving values", ["R_M1C"])
claim("C8_zone_PrZ1", [62, 69, 70, 121], ["P1", "P2"],
      "PrZ1 verdict: SiC attracts Ge at 6.5 A (dE = -0.091 eV; registered prediction of repulsion refuted)",
      FLIP, f"innermost-bin energy {prof[0]['dE_mean']:.3f} eV; a shift of +{-prof[0]['dE_mean']:.3f} eV flips the "
      f"sign, well inside the {SHIFT_EV} eV band",
      "attraction holds (dE between -0.25 and -0.02 eV); P(flip) about 0.3",
      "dE(6.5 A) > +0.01 eV (repulsion, PrZ1 would pass)", ["R_Z1"],
      {"dE_profile_eV": {str(p["bin"]): p["dE_mean"] for p in prof}})
claim("C9_zone_decision", [70, 121], ["P1", "P2"],
      "Si-rich zone recorded as a quantified minor term; carbon claims stand (cancel < 0.2 at R = 2.5 and 5 nm)",
      MAG, f"cancel = {', '.join(f'{v:.2f}' for v in base_cancel.values())} with w_eq = {base_w:.1f} A. Replaying "
      f"the registered formula: a repulsive shift confined to the bins that carry signal (d < {near_cut} A) cannot "
      f"reach the threshold at any size (full Ge depletion there gives w_eq = {near_max_w:.1f} A, cancel "
      f"{max(near_max_cancel.values()):.2f}); only a uniform shift of {zone_flip_shift} eV at every distance out "
      f"to 13.5 A (w_eq = {zone_flip_w} A) flips the branch. Segregation energies are differences against far "
      "sites, and a version change acts on the interface chemistry, so a uniform far-field shift is the "
      "implausible case",
      "branch stays 'strengthen' (cancel < 0.2 at both radii)",
      "cancel >= 0.2 at either radius (branch becomes 'correct'), or |dE| >= 0.1 eV at any bin beyond 9 A", ["R_Z1"],
      {"uniform_shift_needed_eV": zone_flip_shift, "w_eq_at_flip_A": zone_flip_w,
       "near_field_only_max_w_eq_A": round(near_max_w, 2), "near_field_only_max_cancel": near_max_cancel})
claim("C10_party_offset", [1], ["P1", "P2"],
      "MACE-MD kappa sits at 0.55-0.58 x Tersoff at the same box and protocol (the measured party offset)",
      MAG, "Deng et al. (2025) report systematic softening of universal potentials that later, larger training sets "
      "reduce; float32 force noise also lowers kappa; the offset is a level, carried as a scope label",
      "MACE/Tersoff ratio rises (towards 0.7-1.0) at both compositions",
      "ratio falls below 0.55 at either composition", ["R_P4B"])
claim("C11_composition_trend_crossmethod", [1], ["P1"],
      "composition trend kappa(0.15)/kappa(0.5) = 1.81 (MACE) vs 1.71 (Tersoff): alloy scattering is "
      "method-robust",
      MAG, "alloy mass-disorder scattering is set by Si/Ge masses, which no potential changes",
      "ratio within 1.5-2.1", "ratio outside 1.5-2.1", ["R_P4B"])
claim("C12_h2h_mfgp_pick", [63, 66, 67], ["P1"],
      "head-to-head baseline rows that use the two MACE points as middle fidelity: MF-GP pick at 1100 K and the "
      "multi-fidelity BO replay (budget used, pick still moving)",
      FLIP, f"the 1100 K minimum is shallow: x = {flat[0]}-{flat[-1]} lie within 8% of the minimum; MF-GP picks "
      f"{mf_picks} moved when only the MACE level changed (104x unit slip corrected); the pipeline's own answer "
      "does not read MACE",
      "pipeline row unchanged; MF-GP pick moves by at most one grid step (0.05)",
      "pipeline row changes, or an MF-GP pick moves by more than 0.10 in x", ["R_P4B"],
      {"mf_picks": mf_picks, "flat_region_x": [flat[0], flat[-1]]})
claim("C13_P3_Q1", [64, 72, 73], ["P3"],
      "Q1 refuted: covering CA1 (15 runs) predicts hidden MACE-MD recipes no better than random 15-run batches",
      FLIP, f"log RMSE CA1 {sc['CA1']['log_rmse']:.3f} vs random-15 median {sc['RND15']['log_rmse']:.3f} "
      f"(margin {sc['CA1']['log_rmse']-sc['RND15']['log_rmse']:.3f}) is below the replicate-seed noise "
      f"{noise:.3f}; the record's explanation (four of five factors below noise) would keep it refuted",
      "stays refuted (CA1 above the random median) as long as carbon and dopant stay below seed noise",
      "CA1 hidden log RMSE <= random-15 median", ["R_P3"],
      {"margin": sc["CA1"]["log_rmse"] - sc["RND15"]["log_rmse"], "noise": noise})
claim("C14_P3_Q2", [64, 72, 73], ["P3"],
      "Q2 holds: one-factor-at-a-time predicts worse than random 12-run batches",
      FLIP, f"margin {sc['OFAT']['log_rmse']-sc['RND12']['log_rmse']:.3f} in log RMSE, below the seed noise "
      f"{noise:.3f}; pair coverage (54%) and pick regret (40%) are design properties and do not move",
      "holds", "OFAT hidden log RMSE <= random-12 median", ["R_P3"])
claim("C15_P3_Q3", [64, 72, 73], ["P3"],
      "Q3 refuted: dopant ranked 4th of 5 by permutation importance, not last",
      FLIP, f"importances y_C {imp['y_C']:.4f}, dopant {imp['dopant']:.4f}, carbon form {imp['carbon_form']:.4f} "
      "are all below seed noise; their order carries no information and can reorder under any change of the "
      "measurement",
      "Ge content first and temperature second again; the order of the last three changes with probability "
      "about 0.5", "Ge content not ranked first", ["R_P3"], {"importance": imp})
claim("C16_P3_Q4", [64, 72, 73], ["P3"],
      "Q4 holds nominally: dispersed carbon gives lower kappa than clustered (ratio 0.99)",
      FLIP, f"ratio {p3r['predictions']['Q4']['dispersed_over_clustered']:.3f}, 0.008 below the threshold of 1, "
      f"against matched-pair scatter 0.90-1.19",
      "ratio within 0.95-1.05, verdict a coin toss", "ratio outside 0.95-1.05 (carbon form would become a "
      "resolved factor in a 1152-atom box)", ["R_P3"])
claim("C17_P3_Q5", [64, 72, 73], ["P3"],
      "Q5 holds: carbon-free minimum of kappa over x at 300 K lies at x = 0.5",
      MAG, "set by alloy mass disorder, the same physics that kept the party-4b composition ratio method-robust",
      "argmin in [0.3, 0.7]", "argmin outside [0.3, 0.7]", ["R_P3"])
claim("C18_P3_cost_inputs", [], ["P3"],
      "cost inputs: MACE-MD 4.1 h per point (party 4b) and the covering cost weight 246; 'without the MACE runs "
      "the plan drops to 21.8 h'",
      MAG, "cost of a newer checkpoint differs (model size, precision); these are hand-copied constants with no "
      "ledger entry", "cost per point changes; no batch design decision changes", "a P3 batch choice changes "
      "when the measured cost of the new model is substituted", ["R_P4B"])
claim("C19_P2_P08_fault", [4, 5, 14, 81, 84], ["P1", "P2"],
      "planted fault P08 (MACE rows under the Tersoff label) magnitude 0.50-0.60 x and detector-v2 lattice ratio",
      MAG, "the fault study draws P08 from fixed constants copied from party 4b and a MACE lattice calculation; "
      "no registered prediction Pr1-Pr7 of detector v2 reads P08; detection rates (v1 0.68, v2 1.00) would be "
      "re-reported, not re-decided", "detector-v2 adoption (ledger 84) unchanged",
      "a recalibrated P08 changes any of Pr1-Pr7", ["R_P4B", "R_M1C"])
claim("C20_theorist_O3", [122, 123, 124], ["P4", "P5"],
      "open question O3 of the AI-theorist pilot asks exactly this event (theorist A: sign holds, shift > 0.3 eV, "
      "1.3 eV; theorist B: sign holds, within 0.3 eV, 0.4 eV)",
      UNA, "the theorist answers are predictions about this recompute, not results that rest on it; the recompute "
      "grades them", "category 'sign holds, magnitude within 0.3 eV' (theorist B's category)",
      "sign flips, or the magnitude changes by more than 0.3 eV", ["R_M1C"])
claim("C21_light_dopants", [74, 75, 76], ["P1", "P3"],
      "B, P inert; H, D, He minor; cavities a lever; no dopant moves the screening pick",
      UNA, "B/P mass and strain terms come from almaBTE modes; the MACE summary enters only through the "
      "substitutional-carbon strain term, which no dopant row reads", "unchanged", "any class changes", ["R_M1C"])

p4b = sorted(glob.glob(os.path.join(MT, "p4_tskg/T1_md/bench/*.json")))
p4b_a = [json.load(open(f)).get("a0_mace_A") for f in p4b]
p4b_v = [json.load(open(f)).get("a_vegard_A") for f in p4b]
claim("C22_P4_T1_live", [126, 127], ["P4", "P5"],
      "P4 stage T1 MACE-MD of Ge0.88Sn0.12 with vacancies (running; only benchmarks committed)",
      UNA, "no result or decision exists yet; the potential version is a design parameter of this run. The "
           f"benchmarks already show the PBE-family lattice offset: a0 = {', '.join(f'{a:.3f}' for a in p4b_a if a)} A "
           f"against Vegard {p4b_v[0] if p4b_v else 'n/a'} A",
      "every T1 result will need the version label; O1/O2 grades will be version-specific",
      "not applicable until T1 results are ledgered", [])
claim("C23_fault_study_chain", [5, 6, 14, 24, 83], ["P2"],
      "detector code changes and campaign operations reached only through the fault-study code that holds "
      "the P08 constants", UNA, "the P08 constants act on synthetic trials only; the campaign-row operations "
      "(e.g. scope limit near melting, ledger 24) and the detector crash fixes read no MACE value",
      "unchanged", "any campaign-row operation changes after P08 is recalibrated", [])
claim("C24_records_without_mace_quantity", [60, 71], ["P1", "P2"],
      "small-SiC MD gate G1 (Tersoff geometry) and the ledger rehash record",
      UNA, "the gate reads Tersoff particle geometry; the rehash is bookkeeping", "unchanged", "either entry changes",
      [])

# coverage check: every entry reached at T0-T2 must carry a claim or a stated default
claimed = {s for c in C for s in c["ledger_seqs"]}
reached_entries = []
for n in sorted((n for n in full if n.startswith("L:")), key=lambda n: int(n[2:])):
    s = int(n[2:])
    cs = [c["id"] for c in C if s in c["ledger_seqs"]]
    if cs:
        classes = sorted({c["predicted_class"] for c in C if s in c["ledger_seqs"]})
        reason = "see claims"
    elif first_tier[n] == "T3_plus_campaign_names":
        classes, reason = [UNA], "reached only through a shared or parent campaign name; no MACE quantity in its rule"
    elif SEQ[s]["kind"] in ("preregistration", "design", "observation", "deviation", "commitment"):
        classes, reason = [UNA], ("registration, design or protocol record: it fixes the model before output; a "
                                  "rerun with a new version needs a new registration or a deviation, not a "
                                  "change to this entry")
    else:
        classes, reason = [MAG], "MACE value enters as an input; no registered threshold reads it"
    reached_entries.append({"seq": s, "kind": SEQ[s]["kind"], "op_id": SEQ[s]["payload"].get("op_id"),
                            "campaign": CAMP[s], "first_tier": first_tier[n], "claims": cs,
                            "predicted_class": classes, "default_reason": None if cs else reason,
                            "path": path_to(full, n)})

# ---------------------------------------------------------------- minimal recompute set
seedw = {s["id"]: s for s in SEEDS}
p3_med_h = None
try:
    w = sorted(json.load(open(f)).get("wall_s_this_attempt") or 0 for f in glob.glob(os.path.join(MT, "p3_mace/raw/out/*.json")))
    p3_med_h = w[len(w) // 2] / 3600.0
except Exception:
    pass
UNITS = {
    "R_M1C": {"what": "rerun the 51 M1c relaxations (Si, Ge, 3C-SiC bulk; x = 0, 0.2, 0.5 hosts with 0-4 C; "
                      "min/max-Ge shells) with the new model, float64, same gates; then analyze_sigec and "
                      "apply_m1c_decision (seconds)",
              "recorded_cost_h": seedw["MACE_M1C"]["recorded_wall_h"], "unit": seedw["MACE_M1C"]["wall_unit"]},
    "R_Z1": {"what": "rerun the 19 Z1 relaxations (Ge at 6.5-15.5 A from a SiC sphere in a 1728-atom Si cell); "
                     "then analyze_zone (seconds)",
             "recorded_cost_h": seedw["MACE_Z1"]["recorded_wall_h"], "unit": seedw["MACE_Z1"]["wall_unit"]},
    "R_P4B": {"what": "rerun the 2 party-4b MACE-MD points (x = 0.15, 0.5; 300 K; 4x4x24 box); then "
                      "head_to_head.py MF-GP rows and replay (seconds)",
              "recorded_cost_h": seedw["MACE_P4B"]["recorded_wall_h"], "unit": seedw["MACE_P4B"]["wall_unit"]},
    "R_P3": {"what": "rerun all 89 P3 MACE-MD runs (Q3 needs all 71 planner points, Q1/Q2 the 16 hidden, the 2 "
                     "repeats give the noise floor); then analyze_p3_mace (seconds)",
             "recorded_cost_h": seedw["MACE_P3"]["recorded_wall_h"], "unit": seedw["MACE_P3"]["wall_unit"]},
}
flip_items = [c for c in C if c["predicted_class"] == FLIP]
best_set, best_cost = None, None
for k in range(1, len(UNITS) + 1):
    for combo in itertools.combinations(sorted(UNITS), k):
        if all(set(c["settled_by"]) & set(combo) for c in flip_items):
            cost = sum(UNITS[u]["recorded_cost_h"] for u in combo)
            if best_cost is None or cost < best_cost:
                best_set, best_cost = combo, cost
    if best_set:
        break
cpu_h = sum(UNITS[u]["recorded_cost_h"] for u in best_set if "CPU" in UNITS[u]["unit"])
gpu_h = sum(UNITS[u]["recorded_cost_h"] for u in best_set if "GPU" in UNITS[u]["unit"])
staged = {"stage_1_cpu": [u for u in best_set if "CPU" in UNITS[u]["unit"]],
          "stage_2_gpu_small": [u for u in best_set if u == "R_P4B"],
          "stage_3_gpu_large": [u for u in best_set if u == "R_P3"],
          "p3_screen_option": {"what": "before R_P3, run the 2 repeat-seed pairs plus 2 matched carbon-form pairs "
                                       "(6 runs) to measure the new seed noise and carbon contrast; if both stay "
                                       "below noise, Q3/Q4 are predicted to remain uninformative",
                               "recorded_cost_h": round(6 * (p3_med_h or 0), 1), "unit": "GPU-h at the recorded median"}}

# ---------------------------------------------------------------- output
tiers_out = {}
for name, _ in TIERS:
    pr = tier_reach[name]
    tiers_out[name] = {"n_entries": len(entries(pr)), "entries": entries(pr),
                       "n_figure_scripts": sum(1 for n in pr if n.startswith("FIG:"))}
expl = set(tiers_out["T0_explicit"]["entries"])
out = {
    "event": "MACE foundation-potential version change (MACE-MP-0 -> newer checkpoint trained on MPtrj + "
             "Alexandria or OMat, e.g. MACE-MPA-0 / MACE-OMAT-0)",
    "status": "prediction from the record only; no MACE calculation run",
    "ledger_read": {"n_entries": len(E), "last_seq": E[-1]["seq"], "last_time": E[-1]["time"]},
    "record_note_on_versions": "the record carries two checkpoints, not one: MACE-MP-0 medium float64 "
                               "(M1, M1c, Z1) and MACE-MP-0 small float32 (party 4b, P3 MD; p3_mace_design "
                               "says 'MACE-MP-0 small (2023-12-10)'); no file names the 20231203 medium "
                               "checkpoint file, only 'MACE-MP-0 medium' and the CHPC module mace/0.3.16_cu126",
    "plausible_version_shift_eV": SHIFT_EV,
    "seeds": SEEDS + [CONST_SEED],
    "seed_ledger_entries": sorted(s["ledger_seq"] for s in SEEDS),
    "link_type_counts": dict(link_counts),
    "unresolved_parent_campaign_names": unresolved_parents,
    "mace_reading_code": {d: {k: sorted(v) for k, v in m.items()} for d, m in sorted(dir_seeds.items())},
    "reach_by_tier": tiers_out,
    "reach_explicit_vs_inferred": {
        "explicit_only": sorted(expl),
        "added_by_prose_citations": sorted(set(tiers_out["T1_plus_prose_citations"]["entries"]) - expl),
        "added_by_file_paths": sorted(set(tiers_out["T2_plus_file_paths"]["entries"]) -
                                      set(tiers_out["T1_plus_prose_citations"]["entries"])),
        "added_by_campaign_names": sorted(set(tiers_out["T3_plus_campaign_names"]["entries"]) -
                                          set(tiers_out["T2_plus_file_paths"]["entries"])),
    },
    "reached_entries": reached_entries,
    "reached_figure_scripts": sorted(n[4:] for n in full if n.startswith("FIG:")),
    "paper_statements": {"n_lines": len(paper_lines),
                         "by_paper": {p: sum(1 for l in paper_lines if l["paper"] == p) for p in DRAFTS},
                         "by_link": {t: sum(1 for l in paper_lines if l["link"] == t)
                                     for t in ("keyword_MACE", "ledger_citation")},
                         "lines": paper_lines},
    "claims": C,
    "decision_may_flip": [c["id"] for c in flip_items],
    "minimal_recompute_set": {"units": list(best_set), "detail": {u: UNITS[u] for u in best_set},
                              "recorded_cost": {"cpu_task_h": round(cpu_h, 2), "gpu_h": round(gpu_h, 2)},
                              "cost_note": "costs are the recorded wall times of the old checkpoints; P3 and party "
                                           "4b used the small float32 model, so a medium-size newer model will "
                                           "cost more per step; measure with one timing run before submitting",
                              "staging": staged},
    "all_units": UNITS,
}
json.dump(out, open(OUT, "w"), indent=1)

print(json.dumps({"seeds": out["seed_ledger_entries"],
                  "reach": {k: v["n_entries"] for k, v in tiers_out.items()},
                  "explicit_vs_inferred": {k: v for k, v in out["reach_explicit_vs_inferred"].items()},
                  "figure_scripts": len(out["reached_figure_scripts"]),
                  "paper_lines": out["paper_statements"]["by_paper"],
                  "flip": out["decision_may_flip"],
                  "recompute": out["minimal_recompute_set"]["units"],
                  "cost": out["minimal_recompute_set"]["recorded_cost"],
                  "zone_flip_shift_eV": zone_flip_shift,
                  "unresolved_parents": unresolved_parents,
                  "unclaimed_T0_T2": [r["seq"] for r in reached_entries
                                      if not r["claims"] and r["first_tier"] != "T3_plus_campaign_names"]},
                 indent=1))
