#!/usr/bin/env python3
"""S2 + S3: diff the pinned and new SiGe slices curve by curve, re-run the
unchanged ingest and bound screen on the new slice in a parallel folder
(party5_databases/open_db_<tag>/), and report what moves. Writes
version_bump/analysis.json. Run with ~/mat_theory_pilot/venv/bin/python."""
import csv, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
P5 = os.path.dirname(HERE)
TAG = "data-20261003"
OLD = os.path.join(P5, "open_db")
NEW = os.path.join(P5, "open_db_" + TAG)
KEY = ("sample_id", "figure_id", "prop_y")
# values the entry rules read; timestamps and row ids are not evidence
VALUE_FIELDS = ("DOI", "composition", "prop_x", "prop_y", "unit_x", "unit_y", "x", "y")


def strip(row):
    return None if row is None else {k: v for k, v in row.items()
                                     if "updated" not in k and "created" not in k and k != "SID"}


def load(d, name):
    with open(os.path.join(d, name), newline="") as fh:
        return list(csv.DictReader(fh))


def index(rows, key):
    out = {}
    for r in rows:
        out.setdefault(tuple(r.get(k, "") for k in key), []).append(r)
    return out


def main():
    oc = index(load(os.path.join(OLD, "raw"), "starry_sige_kappa_curves.csv"), KEY)
    nc = index(load(os.path.join(HERE, "raw_" + TAG), "starry_sige_kappa_curves.csv"), KEY)
    osm = {r["sample_id"]: r for r in load(os.path.join(OLD, "raw"), "starry_sige_samples.csv")}
    nsm = {r["sample_id"]: r for r in load(os.path.join(HERE, "raw_" + TAG), "starry_sige_samples.csv")}
    added = sorted(set(nc) - set(oc)); removed = sorted(set(oc) - set(nc))
    changed, field_changes = [], {}
    for k in sorted(set(oc) & set(nc)):
        a, b = oc[k], nc[k]
        diff = sorted({f for ra, rb in zip(a, b) for f in VALUE_FIELDS if ra.get(f) != rb.get(f)}
                      | ({"n_rows"} if len(a) != len(b) else set()))
        if strip(osm.get(k[0])) != strip(nsm.get(k[0])):
            diff.append("sample_metadata")
        if diff:
            changed.append(k); field_changes[" | ".join(k)] = diff
    # S3: parallel folder, unchanged code, new slice
    if os.path.exists(NEW):
        shutil.rmtree(NEW)
    os.makedirs(os.path.join(NEW, "raw"))
    for f in ("ingest_open_db.py", "screen_and_plot.py"):
        shutil.copy2(os.path.join(OLD, f), NEW)
    for f in ("starry_sige_kappa_curves.csv", "starry_sige_samples.csv", "starry_sige_papers.csv"):
        shutil.copy2(os.path.join(HERE, "raw_" + TAG, f), os.path.join(NEW, "raw", f))
    shutil.copy2(os.path.join(OLD, "raw", "ucsb_thermoelectrics.json.gz"), os.path.join(NEW, "raw"))
    for f in ("asta_doi_resolution.json",):
        if os.path.exists(os.path.join(OLD, f)):
            shutil.copy2(os.path.join(OLD, f), NEW)
    for s in ("ingest_open_db.py", "screen_and_plot.py"):
        subprocess.run([sys.executable, s], cwd=NEW, check=True, stdout=subprocess.DEVNULL)
    op = json.load(open(os.path.join(OLD, "open_db_points.json")))
    np_ = json.load(open(os.path.join(NEW, "open_db_points.json")))

    def pkey(p):
        return (str(p.get("upstream", {}).get("sample_id")), p["corpusId"], p["snippet_hash"])

    def live(pts):
        return {pkey(p): p for p in pts if not p.get("dedup_suspect") and not p.get("bound_flag")}
    ol, nl = live(op), live(np_)
    moved_pts = [k for k in set(ol) & set(nl)
                 if abs(float(ol[k]["kappa_W_mK"]) - float(nl[k]["kappa_W_mK"])) > 1e-9 or
                 ol[k].get("x_ge") != nl[k].get("x_ge") or ol[k].get("system") != nl[k].get("system")]
    touched_samples = {k[0] for k in added + removed + changed}
    pts_new, pts_gone = sorted(set(nl) - set(ol)), sorted(set(ol) - set(nl))
    outside = [k for k in moved_pts + pts_new + pts_gone if k[0] not in touched_samples]
    osum = json.load(open(os.path.join(OLD, "SCREEN_SUMMARY.json")))
    nsum = json.load(open(os.path.join(NEW, "SCREEN_SUMMARY.json")))
    moved_sum = {}
    for key in osum:
        if osum[key] != nsum.get(key):
            moved_sum[key] = {"old": osum[key], "new": nsum.get(key)}
    def med(s, k, c):
        v = s.get(k, {}).get(c)
        return v[1] if v else None
    rel = []
    for k in ("x02_300K_median_by_system", "x02_900K_median_by_system"):
        for c in osum.get(k, {}):
            a, b = med(osum, k, c), med(nsum, k, c)
            if a and b:
                rel.append(abs(b / a - 1))
    man = json.load(open(os.path.join(HERE, "raw_" + TAG, "manifest.json")))
    import re
    pins = re.findall(r'"(all_\w+\.csv\.gz)":\s*\n\s*"([0-9a-f]{64})"',
                      open(os.path.join(OLD, "ingest_open_db.py")).read())
    pin = dict(pins)
    n_old = sum(len(v) for v in oc.values())
    frac = (len(added) + len(removed) + len(changed)) / max(len(oc), 1)
    out = {"tag_old": "data-20260928", "tag_new": TAG,
           "curves_old": len(oc), "curves_new": len(nc), "rows_old": n_old,
           "added": [" | ".join(k) for k in added], "removed": [" | ".join(k) for k in removed],
           "changed": field_changes, "fraction_touched": round(frac, 4),
           "live_points_old": len(ol), "live_points_new": len(nl),
           "live_points_moved": len(moved_pts), "live_points_added": len(pts_new),
           "live_points_removed": len(pts_gone),
           "touched_sample_ids": sorted(touched_samples),
           "moves_outside_touched_samples": [list(map(str, k)) for k in outside],
           "summary_moved": moved_sum,
           "max_rel_move_x02_medians": round(max(rel), 4) if rel else 0.0}
    if not (added or removed or changed):
        br = "no_change"
    else:
        br = "+".join(b for b, c in (("changed_values", changed), ("removed", removed), ("added", added)) if c)
    out["branch"] = br
    out["reach_check_pass"] = not outside
    out["predictions"] = {
        "PrV1": all(man["full_release"][f]["sha256"] != pin.get(f) for f in man["full_release"]),
        "PrV2": frac <= 0.05,
        "PrV3": (max(rel) if rel else 0.0) < 0.05,
        "PrV4": not outside}
    json.dump(out, open(os.path.join(HERE, "analysis.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("curves_old", "curves_new", "fraction_touched", "branch",
                                           "live_points_moved", "live_points_added", "live_points_removed",
                                           "reach_check_pass", "max_rel_move_x02_medians", "predictions")}, indent=1))


if __name__ == "__main__":
    main()
