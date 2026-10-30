"""Grades the thatgamejam #02 pre-registration (PREREGISTRATION-thatgamejam02.md) from jam_picks.py's entries.csv.
Apache-2.0. By MV2 of Munim, Inc., made with AI agents (Anthropic Claude).

    python jam_picks.py --jam thatgamejam02 --out /out/census --delay 2.5
    python grade_tgj02.py --csv /out/census/entries.csv --out /out/primary
    python grade_tgj02.py --csv /out/census/entries.csv --out /out/sens --exclude-title "Lantern Drift"

The thresholds below were fixed on 2026-10-30, before the jam's submissions closed (2026-11-08 07:59 UTC) and
before any voting. Never change them after that date; report every prediction, whatever the result.
"""
import argparse
import csv
import json
import math
import os

AWARDS = ("Best Overall", "Best Gameplay", "Best Visual Design")  # thatgamecompany's own picks
TOP_HALF = 0.50          # P1: every award winner sits in the community's top half
BEST_OVERALL_TOP = 0.10  # P2: the Best Overall winner sits in the community's top 10%
MEAN_PCT_MAX = 0.30      # P3: the three winners' mean community percentile is at most 0.30
ADJ_TOL = 0.5            # P5: itch's implied rating median matches the real median within 0.5 ratings
AI_SHARE_MIN = 0.29      # P6: share of ranked entries ticking itch's AI disclosure is at least #01's 0.29
BROWSER_RATIO_MIN = 1.3  # P7: browser entries' median ratings are at least 1.3x download-only entries'
ALPHA = 0.05             # P7 (one-sided) and P8 (two-sided)
CORE = ("P1", "P3", "P7")


def norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def as_bool(v):
    return {"true": True, "false": False}.get(str(v).strip().lower())


def load(path, exclude=()):
    drop = {norm(t) for t in exclude}
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if norm(r["title"]) in drop:
                continue
            rows.append({"title": r["title"],
                         "ratings": int(r["ratings"]) if r.get("ratings", "").strip() else None,
                         "scores": json.loads(r["scores"]) if r.get("scores", "").strip() else {},
                         "browser": as_bool(r.get("browser", "")),
                         "content_ai": r.get("content_ai", "").strip()})
    return rows


def community_key(rows):
    keys = {k for r in rows for k in r["scores"]}
    found = [k for k in keys if "community" in k.lower()]
    return found[0] if found else None


def award_key(rows, award):
    keys = {k for r in rows for k in r["scores"]}
    want = norm(award)
    found = sorted(k for k in keys if norm(k).startswith(want))
    return found[0] if found else None


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def mann_whitney(xs, ys):
    """U of xs over ys with the normal approximation (tie-corrected, continuity-corrected).
    Returns (U, p_greater, p_two_sided); 'greater' = xs tend to be larger."""
    n1, n2 = len(xs), len(ys)
    allv = sorted([(v, 0) for v in xs] + [(v, 1) for v in ys])
    ranks = [0.0] * len(allv)
    ties = 0.0
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        t = j - i + 1
        ties += t ** 3 - t
        i = j + 1
    r1 = sum(rk for rk, (_, g) in zip(ranks, allv) if g == 0)
    u = r1 - n1 * (n1 + 1) / 2
    n = n1 + n2
    mu = n1 * n2 / 2
    var = n1 * n2 / 12 * ((n + 1) - ties / (n * (n - 1)))
    if var <= 0:
        return u, 1.0, 1.0
    sd = math.sqrt(var)
    z_g = (u - mu - 0.5) / sd
    z_t = (abs(u - mu) - 0.5) / sd
    p_g = 0.5 * math.erfc(z_g / math.sqrt(2))
    p_t = min(1.0, math.erfc(max(z_t, 0) / math.sqrt(2)))
    return u, p_g, p_t


def grade(rows):
    ck = community_key(rows)
    ranked = [r for r in rows if ck and ck in r["scores"] and r["scores"][ck].get("score") is not None]
    n_ranked = max([len(ranked)] + [r["scores"][ck]["rank"] for r in ranked])
    out = {"community_criterion": ck, "entries": len(rows), "entries_ranked": len(ranked), "predictions": {}}
    P = out["predictions"]

    def pct(r):
        if ck in r["scores"] and r["scores"][ck].get("score") is not None:
            return r["scores"][ck]["rank"] / n_ranked
        return None

    winners = {}
    for a in AWARDS:
        k = award_key(rows, a)
        w = [r for r in rows if k and k in r["scores"] and r["scores"][k].get("rank") == 1]
        winners[a] = [{"title": r["title"], "community_rank": r["scores"][ck]["rank"] if pct(r) is not None else None,
                       "community_pct": round(pct(r), 4) if pct(r) is not None else None} for r in w]
    out["winners"] = winners
    # an award with no winner found, or a winner outside the community ranking, counts AGAINST the predictions
    pcts = {a: [w["community_pct"] if w["community_pct"] is not None else 1.0 for w in ws] or [1.0]
            for a, ws in winners.items()}
    flat = [p for ps in pcts.values() for p in ps]
    P["P1"] = {"text": "all three award winners rank in the community's top half",
               "value": flat, "held": all(p <= TOP_HALF for p in flat)}
    bo = pcts["Best Overall"]
    P["P2"] = {"text": "the Best Overall winner ranks in the community's top 10%",
               "value": bo, "held": all(p <= BEST_OVERALL_TOP for p in bo)}
    mean_pct = sum(flat) / len(flat)
    P["P3"] = {"text": "the award winners' mean community percentile is at most 0.30",
               "value": round(mean_pct, 4), "held": mean_pct <= MEAN_PCT_MAX}
    top = [r["title"] for r in ranked if r["scores"][ck]["rank"] == 1]
    bo_titles = [w["title"] for w in winners["Best Overall"]]
    P["P4"] = {"text": "the Best Overall winner is not the community's #1",
               "value": {"community_1": top, "best_overall": bo_titles},
               "held": bool(bo_titles) and not set(bo_titles) & set(top)}

    counts = [r["ratings"] for r in ranked if r["ratings"] is not None]
    m = median(counts) if counts else None
    implied = [r["ratings"] * (r["scores"][ck]["raw"] / r["scores"][ck]["score"]) ** 2 for r in ranked
               if r["ratings"] and r["scores"][ck].get("raw") and r["scores"][ck]["score"]
               and r["scores"][ck]["score"] < r["scores"][ck]["raw"] - 1e-9]
    im = median(implied) if implied else None
    P["P5"] = {"text": "itch's rating-count adjustment uses the median ratings per entry (within 0.5)",
               "value": {"ratings_median": m, "implied_median": round(im, 3) if im is not None else None,
                         "penalized": len(implied)},
               "held": im is not None and m is not None and abs(im - m) <= ADJ_TOL}

    stated = [r for r in ranked if r["content_ai"] in ("ai", "no-ai", "not stated")]
    share = sum(1 for r in stated if r["content_ai"] == "ai") / len(stated) if stated else 0.0
    P["P6"] = {"text": "at least 29% of ranked entries tick itch's AI disclosure",
               "value": {"share": round(share, 4), "n": len(stated)}, "held": bool(stated) and share >= AI_SHARE_MIN}

    br = [r["ratings"] for r in ranked if r["browser"] is True and r["ratings"] is not None]
    dl = [r["ratings"] for r in ranked if r["browser"] is False and r["ratings"] is not None]
    if br and dl:
        ratio = median(br) / median(dl) if median(dl) else float("inf")
        _, p_g, _ = mann_whitney(br, dl)
        P["P7"] = {"text": "browser entries get at least 1.3x the median ratings of download-only entries "
                           "(and more ratings, one-sided Mann-Whitney p < 0.05)",
                   "value": {"median_browser": median(br), "median_download": median(dl), "ratio": round(ratio, 3),
                             "n_browser": len(br), "n_download": len(dl), "p_greater": round(p_g, 5)},
                   "held": ratio >= BROWSER_RATIO_MIN and p_g < ALPHA}
    else:
        P["P7"] = {"text": "browser entries get more ratings", "value": None, "held": False}

    ai = [r["scores"][ck]["raw"] for r in ranked if r["content_ai"] == "ai" and r["scores"][ck].get("raw") is not None]
    no = [r["scores"][ck]["raw"] for r in ranked if r["content_ai"] == "no-ai" and r["scores"][ck].get("raw") is not None]
    if ai and no:
        _, _, p_t = mann_whitney(ai, no)
        P["P8"] = {"text": "AI-disclosed and no-AI entries' raw community scores do not differ (two-sided p > 0.05)",
                   "value": {"median_ai": median(ai), "median_no_ai": median(no), "n_ai": len(ai), "n_no_ai": len(no),
                             "p_two_sided": round(p_t, 5)},
                   "held": p_t > ALPHA}
    else:
        P["P8"] = {"text": "AI-disclosed vs no-AI raw scores", "value": None, "held": False}

    out["held"] = sum(1 for p in P.values() if p["held"])
    out["core_held"] = sum(1 for k in CORE if P[k]["held"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude-title", action="append", default=[])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = grade(load(a.csv, a.exclude_title))
    res["excluded_titles"] = a.exclude_title
    with open(os.path.join(a.out, "grade.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    for k, p in res["predictions"].items():
        print("%s %s: %s  %s" % (k, "HELD" if p["held"] else "FAILED", p["text"], json.dumps(p["value"])))
    print("held %d of 8; core (P1, P3, P7) held %d of 3" % (res["held"], res["core_held"]))


if __name__ == "__main__":
    main()
