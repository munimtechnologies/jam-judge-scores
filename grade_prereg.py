"""Grade the pre-registered Slapjam #2 predictions (PREREGISTRATION-slapjam2.md) against a jam_census
entries.csv (Apache-2.0). By MV2 of Munim, Inc., made with AI agents (Anthropic Claude).

    python grade_prereg.py --csv entries.csv --out /out [--perms 20000] [--seed 1] [--exclude-title TITLE]

The thresholds below were fixed on 2026-10-29, before Slapjam #2 opened (15:00 UTC) and before any entry
existed. They come from the Slapjam #1 findings, loosened for judge noise; never edit them after that date.
Every prediction is graded on the entries that have all three criteria scores. Overall is the equal-weight
mean of Fun, Visual Appeal and Theme Following, as the jam page says. Writes grade.json. Standard library only.
"""
import argparse
import csv
import json
import os
import random

import jam_census as jc
import tools_check as tc

SCORES = ["fun_score", "visual_appeal_score", "theme_following_score"]
NONE = "None of these"
EPS = 1e-9

# fixed 2026-10-29 ~02:45Z; Slapjam #1 values in the comments
ENTRIES_RANGE = (50, 145)       # 137 scored entries in #1; #2 had 222 joined vs 312 developers in #1
MIN_PEARSON = 0.50              # #1: 0.64 / 0.67 / 0.72
TOP5_MIN_THEME = 3.8            # #1: every top-5 entry had Theme >= 4.0
TOP5_MIN_ANY = 3.5              # #1: no top-5 criterion under 3.7
RANK5_RANGE = (3.6, 4.3)        # #1: rank-5 Overall 3.95
MAX_ABS_RATINGS_FUN = 0.20      # #1: Spearman(ratings, Fun) -0.002
TOOLS_MIN_GROUP = 10            # #1: 30 tools-only vs 99 none-only
ALPHA = 0.05
CORE = ["H1", "H2", "H4", "H5"]


def load(path, exclude=()):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not all(r.get(k) for k in SCORES) or r["title"] in exclude:
                continue  # the jam's own page has no scores
            row = {"title": r["title"], "ratings": int(r["ratings"]) if r.get("ratings") else None}
            for k in SCORES:
                row[k] = float(r[k])
            row["overall"] = sum(row[k] for k in SCORES) / len(SCORES)
            row["answers"] = json.loads(r.get("answers") or "{}")
            rows.append(row)
    return rows


def tools_question(rows):
    """The tools checklist: the question whose answers hold "None of these" most often (the wording may change)."""
    counts = {}
    for r in rows:
        for q, a in r["answers"].items():
            if NONE in tc.parts(a):
                counts[q] = counts.get(q, 0) + 1
    return max(sorted(counts), key=lambda q: counts[q]) if counts else None


def mean(xs):
    return sum(xs) / len(xs)


def grade(rows, perms=20000, seed=1):
    out = []

    def add(pid, claim, value, held):
        out.append({"id": pid, "claim": claim, "value": value, "held": held})

    n = len(rows)
    add("H0", "scored entries between %d and %d" % ENTRIES_RANGE, n, ENTRIES_RANGE[0] <= n <= ENTRIES_RANGE[1])

    cors = {}
    for i in range(len(SCORES)):
        for j in range(i + 1, len(SCORES)):
            p = jc.pearson([r[SCORES[i]] for r in rows], [r[SCORES[j]] for r in rows])
            cors["%s~%s" % (SCORES[i], SCORES[j])] = round(p, 3) if p is not None else None
    add("H1", "every pairwise Pearson correlation of the three criteria >= %.2f" % MIN_PEARSON, cors,
        all(c is not None and c >= MIN_PEARSON for c in cors.values()))

    means = {k: round(mean([r[k] for r in rows]), 3) for k in SCORES}
    fun, vis, theme = (mean([r[k] for r in rows]) for k in SCORES)
    add("H2", "Theme Following has the highest mean of the three criteria", means, theme > fun and theme > vis)
    add("H3", "Fun has a lower mean than Visual Appeal", means, fun < vis)

    top_overall = max(r["overall"] for r in rows)
    top_fun = max(r["fun_score"] for r in rows)
    winners = [r for r in rows if r["overall"] >= top_overall - EPS]
    add("H4", "the Overall #1 entry is not the top-Fun entry (no entry tied for Overall #1 has the top Fun score)",
        {"overall_1": [r["title"] for r in winners], "overall_1_fun": [r["fun_score"] for r in winners],
         "top_fun": top_fun},
        all(r["fun_score"] < top_fun - EPS for r in winners))

    ranked = sorted(rows, key=lambda r: -r["overall"])
    rank5 = ranked[min(4, n - 1)]["overall"]
    top5 = [r for r in ranked if r["overall"] >= rank5 - EPS]  # ties at 5th are all kept
    add("H5", "every top-5 Overall entry has Theme >= %.1f and no criterion under %.1f" % (TOP5_MIN_THEME, TOP5_MIN_ANY),
        [{"title": r["title"], **{k: r[k] for k in SCORES}} for r in top5],
        all(r["theme_following_score"] >= TOP5_MIN_THEME - EPS and min(r[k] for k in SCORES) >= TOP5_MIN_ANY - EPS
            for r in top5))
    add("H6", "the rank-5 Overall score is between %.2f and %.2f" % RANK5_RANGE, round(rank5, 3),
        RANK5_RANGE[0] <= rank5 <= RANK5_RANGE[1])

    rated = [r for r in rows if r["ratings"] is not None]
    s = jc.spearman([r["ratings"] for r in rated], [r["fun_score"] for r in rated]) if len(rated) >= 3 else None
    add("H7", "|Spearman(ratings count, Fun)| < %.2f" % MAX_ABS_RATINGS_FUN, round(s, 3) if s is not None else None,
        None if s is None else abs(s) < MAX_ABS_RATINGS_FUN)

    q = tools_question(rows)
    groups = {}
    for r in rows:
        groups.setdefault(tc.group(tc.parts(r["answers"].get(q, "")) if q else []), []).append(r)
    tools, nones = groups.get("tools_only", []), groups.get("none_only", [])
    value = {"question": q, "groups": {g: len(rs) for g, rs in sorted(groups.items())}}
    held = None  # not testable with a group under TOOLS_MIN_GROUP
    if len(tools) >= TOOLS_MIN_GROUP and len(nones) >= TOOLS_MIN_GROUP:
        rng = random.Random(seed)
        tests = []
        for m in SCORES + ["overall"]:
            diff, p = tc.perm_test([r[m] for r in tools], [r[m] for r in nones], perms, rng)
            tests.append({"measure": m, "tools_minus_none": round(diff, 3), "p": round(p, 4)})
        for t, adj in zip(tests, tc.holm([t["p"] for t in tests])):
            t["p_holm"] = round(adj, 4)
        value.update({"permutations": perms, "seed": seed, "tests": tests})
        held = all(t["p_holm"] >= ALPHA for t in tests)
    add("H8", "tools-only vs none-only: no criterion or Overall differs at Holm-adjusted p < %.2f" % ALPHA, value, held)
    return out


def verdict(results):
    by = {r["id"]: r["held"] for r in results}
    graded = [r for r in results if r["held"] is not None]
    core = [by[i] for i in CORE]
    return {"held": sum(1 for r in graded if r["held"]), "graded": len(graded),
            "not_testable": [r["id"] for r in results if r["held"] is None],
            "core": CORE, "core_replicated": all(c is True for c in core)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--perms", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--exclude-title", action="append", default=[], help="sensitivity run without these entries")
    a = ap.parse_args(argv)
    results = grade(load(a.csv, a.exclude_title), a.perms, a.seed)
    report = {"results": results, "verdict": verdict(results), "excluded_titles": a.exclude_title}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "grade.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
