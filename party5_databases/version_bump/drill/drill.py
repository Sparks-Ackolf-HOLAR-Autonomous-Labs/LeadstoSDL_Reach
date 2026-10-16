#!/usr/bin/env python3
"""Release-update drill: exercise the correct, quarantine and screen branches
of the registered release-update rule (design.json, ledger seq 92) on a test
release built from the committed slice, and check that the reach check
catches a pipeline fault.

Everything runs on a scratch copy (/tmp/vbdrill); the campaign ledger and
the committed evidence are not touched. Two scenarios:

  A  data change: one live curve scaled by 1.5 (an upstream value correction),
     one live curve removed, one live curve re-published under a new sample id
     (plausible new evidence), and one copy with kappa x20 (a digitising error
     the bound screen must catch).
  B  pipeline fault: the release is unchanged but the ingest copy silently
     drops every point above 800 K; the reach check must fail.

For A the branch actions are written to the scratch ledger by
apply_branches(), the general form of apply.py (which only handles
no_change). Output: drill_results.json next to this script.
Run with ~/mat_theory_pilot/venv/bin/python drill.py
"""
import csv, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCR = "/tmp/vbdrill/mat_theory"
TAG = "drill"


def scratch():
    if os.path.exists("/tmp/vbdrill"):
        shutil.rmtree("/tmp/vbdrill")
    for d in ("party5_databases", "party4_bte", "pilot/src", "pilot/kg"):
        shutil.copytree(os.path.join(MT, d), os.path.join(SCR, d),
                        ignore=shutil.ignore_patterns("drill", "open_db_data-*", "__pycache__"))
    os.makedirs(os.path.join(SCR, "phase_c"))
    shutil.copy2(os.path.join(MT, "phase_c", "ledger_campaign.jsonl"), os.path.join(SCR, "phase_c"))
    vb = os.path.join(SCR, "party5_databases", "version_bump")
    src = open(os.path.join(vb, "diff_propagate.py")).read().replace('TAG = "data-20261003"', f'TAG = "{TAG}"')
    open(os.path.join(vb, "diff_propagate.py"), "w").write(src)
    return vb


def read(p):
    with open(p, newline="", encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        return r.fieldnames, list(r)


def write(p, fields, rows):
    with open(p, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def build_release(vb, scenario):
    src = os.path.join(vb, "raw_data-20261003")
    dst = os.path.join(vb, "raw_" + TAG)
    shutil.copytree(src, dst)
    if scenario != "A":
        return {}
    pts = json.load(open(os.path.join(MT, "party5_databases", "open_db", "open_db_points.json")))
    live = sorted({str(p["upstream"].get("sample_id")) for p in pts
                   if not p.get("dedup_suspect") and not p.get("bound_flag")}, key=int)
    f, curves = read(os.path.join(dst, "starry_sige_kappa_curves.csv"))
    sf, samples = read(os.path.join(dst, "starry_sige_samples.csv"))
    kc = [i for i, r in enumerate(curves) if r["sample_id"] in live and "thermal conductivity" in r["prop_y"].lower()]
    # deterministic picks spread over the live list
    i_chg, i_rm, i_add = kc[len(kc) // 5], kc[len(kc) // 2], kc[4 * len(kc) // 5]
    plan = {"changed": curves[i_chg]["sample_id"], "removed": curves[i_rm]["sample_id"],
            "added_from": curves[i_add]["sample_id"]}
    ys = json.loads(curves[i_chg]["y"])
    curves[i_chg]["y"] = json.dumps([round(v * 1.5, 6) for v in ys])
    new = []
    for sid, scale in (("990001", 1.0), ("990002", 20.0)):
        r = dict(curves[i_add]); r["sample_id"] = sid
        r["y"] = json.dumps([round(v * scale, 6) for v in json.loads(r["y"])])
        new.append(r)
        s = dict(next(x for x in samples if x["sample_id"] == curves[i_add]["sample_id"]))
        s["sample_id"] = sid
        samples.append(s)
    curves = [r for i, r in enumerate(curves) if i != i_rm] + new
    write(os.path.join(dst, "starry_sige_kappa_curves.csv"), f, curves)
    write(os.path.join(dst, "starry_sige_samples.csv"), sf, samples)
    plan["added"] = ["990001 (same values)", "990002 (kappa x20)"]
    return plan


def inject_fault(vb):
    p = os.path.join(os.path.dirname(vb), "open_db", "ingest_open_db.py")
    s = open(p).read()
    s = s.replace('(HERE / "open_db_points.json").write_text(json.dumps(points, indent=1))',
                  'points = [q for q in points if q["T_K"] <= 800]\n'
                  '    (HERE / "open_db_points.json").write_text(json.dumps(points, indent=1))')
    open(p, "w").write(s)


def apply_branches(vb, a):
    """General decision step for the registered rule (scratch ledger only)."""
    sys.path.insert(0, os.path.join(SCR, "pilot", "src"))
    from ledger import Ledger
    led = Ledger(os.path.join(SCR, "phase_c", "ledger_campaign.jsonl"))
    if not a["reach_check_pass"]:
        e = led.append("deviation", {"op_id": "drill-gate-failure", "drill": True,
                                     "statement": "reach check failed: movement outside touched hyperedges",
                                     "outside": a["moves_outside_touched_samples"][:20]})
        return [e["seq"]], led.verify_chain()
    pts = json.load(open(os.path.join(os.path.dirname(vb), "open_db_" + TAG, "open_db_points.json")))
    by_sid = {}
    for p in pts:
        by_sid.setdefault(str(p["upstream"].get("sample_id")), []).append(p)
    seqs = []
    for k, fields in a["changed"].items():
        sid = k.split(" | ")[0]
        seqs.append(led.append("shard_operation", {
            "op": "correct", "drill": True, "target": f"DB-STARRY sample {sid}",
            "cause": "upstream release revised the values", "fields": fields,
            "n_points": len(by_sid.get(sid, []))})["seq"])
    for k in a["removed"]:
        seqs.append(led.append("shard_operation", {
            "op": "quarantine", "drill": True, "target": f"DB-STARRY sample {k.split(' | ')[0]}",
            "cause": "curve withdrawn upstream; reversible, not deleted"})["seq"])
    for k in a["added"]:
        sid = k.split(" | ")[0]
        flagged = any(p.get("bound_flag") for p in by_sid.get(sid, []))
        seqs.append(led.append("shard_operation", {
            "op": "quarantine" if flagged else "retain", "drill": True,
            "target": f"DB-STARRY sample {sid} (new upstream curve)",
            "cause": "fails the cross-party bound screen" if flagged else "passes the bound screen; enters as new evidence"})["seq"])
    return seqs, led.verify_chain()


def run(scenario):
    vb = scratch()
    plan = build_release(vb, scenario)
    if scenario == "B":
        inject_fault(vb)
    subprocess.run([sys.executable, "diff_propagate.py"], cwd=vb, check=True, stdout=subprocess.DEVNULL)
    a = json.load(open(os.path.join(vb, "analysis.json")))
    seqs, chain = apply_branches(vb, a)
    led = [json.loads(l) for l in open(os.path.join(SCR, "phase_c", "ledger_campaign.jsonl"))]
    npts = json.load(open(os.path.join(SCR, "party5_databases", "open_db_" + TAG, "open_db_points.json")))
    touched = {}
    for q in npts:
        sid = str(q["upstream"].get("sample_id"))
        if sid in a["touched_sample_ids"]:
            t = touched.setdefault(sid, {"points": 0, "bound_flagged": 0, "dedup_suspect": 0})
            t["points"] += 1; t["bound_flagged"] += bool(q.get("bound_flag")); t["dedup_suspect"] += bool(q.get("dedup_suspect"))
    return {"plan": plan, "branch": a["branch"], "touched_samples_new_release": touched, "reach_check_pass": a["reach_check_pass"],
            "changed": a["changed"], "removed": a["removed"], "added": a["added"],
            "live_points": [a["live_points_old"], a["live_points_new"]],
            "live_points_moved_added_removed": [a["live_points_moved"], a["live_points_added"],
                                                a["live_points_removed"]],
            "moves_outside_touched_samples": len(a["moves_outside_touched_samples"]),
            "summary_moved": sorted(a["summary_moved"]),
            "max_rel_move_x02_medians": a["max_rel_move_x02_medians"],
            "scratch_ledger_ops": [{k: led[s][k] for k in ("seq", "kind")} | {
                "op": led[s]["payload"].get("op"), "target": led[s]["payload"].get("target"),
                "cause": led[s]["payload"].get("cause", led[s]["payload"].get("statement"))} for s in seqs],
            "scratch_chain_valid": chain}


if __name__ == "__main__":
    out = {"A_data_change": run("A"), "B_pipeline_fault": run("B"),
           "note": "scratch copy only; campaign ledger untouched"}
    json.dump(out, open(os.path.join(HERE, "drill_results.json"), "w"), indent=1)
    for k in ("A_data_change", "B_pipeline_fault"):
        r = out[k]
        print(k, r["branch"], "reach", r["reach_check_pass"], "outside", r["moves_outside_touched_samples"],
              "ops", [(o["op"], o["target"]) for o in r["scratch_ledger_ops"]][:6])
