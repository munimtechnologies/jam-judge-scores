"""Did entries that used a sponsor AI tool score differently in an itch.io jam? (Apache-2.0)
By MV2 of Munim, Inc., made with AI agents (Anthropic Claude).

    python tools_check.py --csv entries.csv --out /out [--perms 20000] [--seed 1]

Reads the entries.csv written by jam_census 0.2.0 and splits the entries by their answer to the tools
checklist ("Which of these did your game use?"): "None of these" only, one or more tools only, both at once
(a contradictory answer, often every box ticked) and no answer. Compares tools-only with none-only on each
criterion and on the equal-weight overall, with a two-sided permutation test on the difference of means and
Holm's correction across the four tests. Contradictory answers are kept out of both groups, which is the
point: jam_census 0.2.0's per-tool means counted them as users of every tool they ticked.
Writes tools.json. Uses only the standard library.
"""
import argparse
import csv
import json
import os
import random

QUESTION = "Which of these did your game use?"
NONE = "None of these"
SCORES = ["fun_score", "visual_appeal_score", "theme_following_score"]
MEASURES = SCORES + ["overall"]


def parts(answer):
    return [p.strip() for p in answer.split(",") if p.strip()]


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["fun_score"]:
                continue  # the jam's own page has no scores
            row = {"title": r["title"], "ratings": int(r["ratings"])}
            for k in SCORES:
                row[k] = float(r[k])
            row["overall"] = sum(row[k] for k in SCORES) / len(SCORES)
            row["adjusted"] = any(r[k] != r[k.replace("_score", "_raw")] for k in SCORES)
            row["parts"] = parts(json.loads(r["answers"] or "{}").get(QUESTION, ""))
            rows.append(row)
    return rows


def group(p):
    if not p:
        return "no_answer"
    tools = [x for x in p if x != NONE]
    if not tools:
        return "none_only"
    return "contradictory" if NONE in p else "tools_only"


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def perm_test(a, b, perms, rng):
    """Two-sided permutation p-value for mean(a) - mean(b), with the +1 correction."""
    diff = mean(a) - mean(b)
    pool = list(a) + list(b)
    n = len(a)
    hits = 0
    for _ in range(perms):
        rng.shuffle(pool)
        if abs(mean(pool[:n]) - mean(pool[n:])) >= abs(diff) - 1e-12:
            hits += 1
    return diff, (hits + 1) / (perms + 1)


def holm(ps):
    """Holm-adjusted p-values, in the input order."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out = [0.0] * len(ps)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = running
    return out


def analyse(rows, perms=20000, seed=1):
    groups = {}
    for r in rows:
        groups.setdefault(group(r["parts"]), []).append(r)
    summary = {"entries": len(rows), "groups": {}}
    for g, rs in sorted(groups.items()):
        summary["groups"][g] = {"entries": len(rs)}
        for m in MEASURES:
            summary["groups"][g]["mean_" + m] = round(mean([r[m] for r in rs]), 3)
    summary["contradictory_titles"] = [r["title"] for r in groups.get("contradictory", [])]
    summary["adjusted_titles"] = [r["title"] for r in rows if r["adjusted"]]

    tools, nones = groups.get("tools_only", []), groups.get("none_only", [])
    rng = random.Random(seed)
    tests = []
    for m in MEASURES:
        diff, p = perm_test([r[m] for r in tools], [r[m] for r in nones], perms, rng)
        tests.append({"measure": m, "tools_minus_none": round(diff, 3), "p": round(p, 4)})
    for t, adj in zip(tests, holm([t["p"] for t in tests])):
        t["p_holm"] = round(adj, 4)
    summary["tools_only_vs_none_only"] = {"permutations": perms, "seed": seed, "tests": tests}

    # each tool on its own, consistent answers only: descriptive, the groups are too small to test
    per_tool = {}
    for r in tools:
        for t in r["parts"]:
            per_tool.setdefault(t, []).append(r)
    summary["per_tool_consistent"] = {
        t: {"entries": len(rs), "mean_overall": round(mean([r["overall"] for r in rs]), 3)}
        for t, rs in sorted(per_tool.items(), key=lambda kv: -len(kv[1]))}

    ranked = sorted(rows, key=lambda r: -r["overall"])
    summary["top20_overall_by_group"] = {}
    for r in ranked[:20]:
        g = group(r["parts"])
        summary["top20_overall_by_group"][g] = summary["top20_overall_by_group"].get(g, 0) + 1
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--perms", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    summary = analyse(load(a.csv), a.perms, a.seed)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "tools.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
