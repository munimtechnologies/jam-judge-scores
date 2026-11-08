# explore_h7.py: EXPLORATORY (not pre-registered) follow-up to Slapjam #2 prediction H7.
# H7 was graded on itch.io's adjusted Fun score. itch scales an entry's score down when it has
# fewer ratings than the jam's median, so adjusted scores are mechanically tied to the ratings
# count. This script repeats the test on the RAW Fun score and reports how many entries were scaled.
# Apache-2.0. MV2, Munim, Inc., mv2@munimtech.com. Made with AI agents (Anthropic Claude).
import argparse
import csv
import json
import os
import statistics


def ranks(values):
    """Average ranks (1-based), ties share the mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = r
        i = j + 1
    return out


def pearson(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / (sxx * syy) ** 0.5


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def load(path, exclude=()):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["title"] in exclude:
                continue
            try:
                rows.append({
                    "ratings": int(r["ratings"]),
                    "fun_score": float(r["fun_score"]),
                    "fun_raw": float(r["fun_raw"]),
                    "visual_raw": float(r["visual_appeal_raw"]),
                    "theme_raw": float(r["theme_following_raw"]),
                })
            except (KeyError, ValueError):
                continue
    return rows


def analyse(rows):
    n = [r["ratings"] for r in rows]
    med = statistics.median(n)
    scaled = sum(1 for r in rows if abs(r["fun_score"] - r["fun_raw"]) > 1e-9)
    counts = {}
    for k in n:
        counts[str(k)] = counts.get(str(k), 0) + 1
    out = {
        "entries": len(rows),
        "median_ratings": med,
        "ratings_histogram": dict(sorted(counts.items(), key=lambda kv: int(kv[0]))),
        "entries_with_fun_adjusted": scaled,
        "spearman_ratings_vs_fun_adjusted": round(spearman(n, [r["fun_score"] for r in rows]), 3),
        "spearman_ratings_vs_fun_raw": round(spearman(n, [r["fun_raw"] for r in rows]), 3),
        "spearman_ratings_vs_visual_raw": round(spearman(n, [r["visual_raw"] for r in rows]), 3),
        "spearman_ratings_vs_theme_raw": round(spearman(n, [r["theme_raw"] for r in rows]), 3),
    }
    at_or_above = [r for r in rows if r["ratings"] >= med]
    if len(at_or_above) >= 10:
        out["at_or_above_median_entries"] = len(at_or_above)
        out["spearman_ratings_vs_fun_raw_at_or_above_median"] = round(
            spearman([r["ratings"] for r in at_or_above], [r["fun_raw"] for r in at_or_above]), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude-title", action="append", default=[])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = {"label": "EXPLORATORY, not pre-registered", "excluded_titles": a.exclude_title,
           "result": analyse(load(a.csv, a.exclude_title))}
    with open(os.path.join(a.out, "explore_h7.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
