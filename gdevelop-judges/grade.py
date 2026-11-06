# grade.py: grade the pre-registered GDevelop judges' reach predictions (P1-P6) from judge_reach.py output.
#
# By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents (Anthropic Claude) working in his
# name. Apache-2.0.
#
#   python grade.py --picks picks.csv --jams jams.csv [--fixes fixes.csv] [--entries-dir entries]
#
# picks.csv and jams.csv are judge_reach.py 0.2.2 output. fixes.csv lists manual title fixes, each one
# a candidate the script itself listed (the pre-registration's rule); with --entries-dir the fixed row's
# rank and ratings are read from entries/<slug>.csv by rate_id. Prints JSON with every count and the
# verdict for each prediction, once for the automatic matches and once with the fixes applied.

import argparse
import csv
import json
import os
import statistics
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def apply_fixes(picks, fixes, jams, entries_dir):
    """Return a copy of picks with each fix filled in from the jam's entries file (matched by rate_id)."""
    slug = {int(j["jam"]): j["slug"] for j in jams}
    out = [dict(p) for p in picks]
    for fx in fixes:
        jam, place = int(fx["jam"]), int(fx["place"])
        rows = load(os.path.join(entries_dir, slug[jam] + ".csv"))
        hit = [r for r in rows if r["rate_id"] == fx["chosen_rate_id"]]
        if len(hit) != 1:
            raise ValueError("fix for jam %d place %d: rate_id %s not found once" % (jam, place, fx["chosen_rate_id"]))
        e = hit[0]
        if e["title"] != fx["chosen_title"]:
            raise ValueError("fix for jam %d place %d: title %r != %r" % (jam, place, e["title"], fx["chosen_title"]))
        for p in out:
            if int(p["jam"]) == jam and int(p["place"]) == place:
                if p["rank"] != "":
                    raise ValueError("fix for jam %d place %d: pick already matched" % (jam, place))
                p.update({"matched_title": e["title"], "match": "manual", "rank": e["rank"],
                          "ratings": e["ratings"], "score": e["score"], "raw": e["raw"]})
    return out


def grade(picks, jams):
    found = [p for p in picks if p["rank"] != ""]
    n = len(found)
    ranks = sorted(int(p["rank"]) for p in found)
    below = sum(1 for p in found if float(p["ratings"]) < float(p["median_ratings_ranked"]))
    top30 = sum(1 for r in ranks if r <= 30)
    displaced = [int(j["raw_top_displaced"]) for j in jams if j.get("raw_top_displaced", "") != ""]
    jams_disp = sum(1 for d in displaced if d >= 1)
    gradable = n >= 40
    res = {
        "matched": n, "picks": len(picks), "core_gradable": gradable,
        "in_top_10": sum(1 for r in ranks if r <= 10), "in_top_30": top30,
        "share_top_30": round(top30 / n, 4) if n else None,
        "below_median": below, "share_below_median": round(below / n, 4) if n else None,
        "jams_with_displacement": jams_disp, "jams": len(displaced),
        "worst_rank": max(ranks) if ranks else None,
        "median_rank": statistics.median(ranks) if ranks else None,
        "fewest_ratings": min(int(p["ratings"]) for p in found) if found else None,
        "ranks_worse_than_30": [r for r in ranks if r > 30],
    }
    res["P1"] = (top30 / n >= 0.85) if gradable else None
    res["P2"] = (below / n < 0.20) if gradable else None
    res["P3"] = (jams_disp >= 6) if gradable else None
    res["P4"] = res["worst_rank"] <= 60 if ranks else None
    res["P5"] = res["median_rank"] <= 10 if ranks else None
    res["P6"] = res["fewest_ratings"] >= 5 if found else None
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True)
    ap.add_argument("--jams", required=True)
    ap.add_argument("--fixes", default="")
    ap.add_argument("--entries-dir", default="")
    a = ap.parse_args(argv)
    picks, jams = load(a.picks), load(a.jams)
    out = {"automatic": grade(picks, jams)}
    if a.fixes:
        fixed = apply_fixes(picks, load(a.fixes), jams, a.entries_dir)
        out["with_fixes"] = grade(fixed, jams)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
