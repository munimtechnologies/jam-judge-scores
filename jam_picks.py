"""Hand-picked vs community census of one itch.io jam (Apache-2.0). By MV2 of Munim, Inc., made with AI agents
(Anthropic Claude).

    python jam_picks.py --jam thatgamejam01 --out /out [--delay 1.5] [--raw-dir DIR] [--no-game-pages]

Reads only public pages that itch.io's robots.txt allows: the jam's results pages (every criterion), each
entry's /jam/<jam>/rate/<id> page and the game page it links to (never download pages), one request every
--delay seconds, with a User-Agent that names MV2 and his email. Saves every page it read under out/raw/ so the
parse can be redone offline (--raw-dir reuses them without any network). Writes entries.csv (author handles and
game URLs stay out; only a team-size count is kept) and summary.json: which criteria the host hand-picked
(every score "n/a") and which were rated, where the hand-picked entries sit in the rated ranking, how they
differ from the rest (browser play, itch's AI disclosure, team size, engine), and a check of itch's
rating-count adjustment (below the jam's median, score = raw * sqrt(ratings / median)).

0.2.0 (2026-10-17): follows the results pages' relative "?page=N" links (0.1.0 read only page 1 of each
view), and detects browser play from the embed's own markup (0.1.0 also matched itch's CSS, so every game
looked browser-playable).
"""
import argparse
import csv
import html
import json
import math
import os
import random
import re
import sys
import time
import urllib.request

BASE = "https://itch.io"
UA = "MV2-Munim-jam-picks/0.2 (MV2 of Munim, Inc.; mv2@munimtech.com)"
INFO_LABELS = ("Status", "Platforms", "Author", "Authors", "Genre", "Made with", "Tags", "Content",
               "AI Disclosure", "Average session", "Languages", "Inputs", "Accessibility")
SCORE = re.compile(r"#(\d+)\s+(n/a|\d+(?:\.\d+)?)\s+(n/a|\d+(?:\.\d+)?)")
GAME_URL = re.compile(r'href="(https://([a-z0-9][a-z0-9_-]*)\.itch\.io/[a-z0-9][a-z0-9_-]*)/?"', re.I)
NOT_GAME_HOSTS = {"static", "img", "www", "embed", "html"}
RUN_GAME = re.compile(r'id="html_embed_\d+"|class="iframe_placeholder"|\bload_iframe_btn\b|id="view_html_game_\d+"')
AI_WORDS = re.compile(r"\bA\.?I\b|(?i:artificial intelligence|generative ai|\bgen ?ai\b|chatgpt|midjourney|"
                      r"stable diffusion|\bsuno\b|elevenlabs|copilot|\bllm)")
PREREGISTERED = {  # feature, direction of the test (see PREREG.md)
    "H1_ai_disclosed_fewer_among_picks": ("ai_disclosed_itch", "less"),
    "H2_browser_share_differs": ("browser", "two"),
    "H3_teams_more_among_picks": ("team_2plus", "greater"),
}


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # retry, then give up loudly
            last = e
            time.sleep(5 * (i + 1))
    raise last


def to_text(h):
    """Visible text with one line per block and a tab after every table cell."""
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    h = re.sub(r"\s+", " ", h)
    h = re.sub(r"(?i)</t[dh]>", "\t", h)
    h = re.sub(r"(?i)<br\s*/?>|</(?:p|div|tr|li|h\d|table|section|dt|dd)>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    lines = [re.sub(r"[  ]+", " ", ln).strip() for ln in h.split("\n")]
    return "\n".join(ln for ln in lines if ln.strip("\t "))


def rate_ids(page_html, jam):
    """Entry ids linked from a results page, in page order, without repeats."""
    return list(dict.fromkeys(re.findall(r"/jam/%s/rate/(\d+)" % re.escape(jam), page_html)))


def criteria_slugs(page_html, jam):
    """Slugs of the per-criterion results views linked from the main results page."""
    return list(dict.fromkeys(re.findall(r"/jam/%s/results/([a-z0-9][a-z0-9-]*)" % re.escape(jam), page_html)))


def page_count(page_html, path):
    """Pages of one results view: ?page= links on that exact path, or relative href="?page=N" links (itch's
    pager), which always point at the page's own view."""
    nums = [int(n) for n in re.findall(re.escape(path) + r"\?page=(\d+)", page_html)]
    nums += [int(n) for n in re.findall(r'href="\?page=(\d+)"', page_html)]
    return max(nums) if nums else 1


def game_title(page_title):
    """'Game by author for Jam - itch.io' -> 'Game' (author handles stay out of the data)."""
    m = re.match(r"(.*) by .+? for .+ - itch\.io$", page_title)
    if m:
        return m.group(1)
    return re.sub(r"\s*-\s*itch\.io$", "", page_title)


def num(s):
    return None if s == "n/a" else float(s)


def score_rows(text):
    """{criterion: {rank, score, raw}} from a rate page's results table; a hand-picked row has score None."""
    end = text.find("Ranked from")
    end = end if end >= 0 else len(text)
    start = text.rfind("Criteria", 0, end)
    if start < 0:
        return {}
    seg = text[start:end]
    rows = {}
    for m in SCORE.finditer(seg):
        before = [p.strip() for p in re.split(r"[\t\n]", seg[:m.start()]) if p.strip()]
        name = before[-1] if before else ""
        if name and len(name) <= 80 and name not in rows:
            rows[name] = {"rank": int(m.group(1)), "score": num(m.group(2)), "raw": num(m.group(3))}
    return rows


def page_title(h):
    m = re.search(r"(?is)<title>(.*?)</title>", h)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


def parse_rate_page(h):
    text = to_text(h)
    row = {"title": game_title(page_title(h)), "ratings": None, "scores": score_rows(text), "game_url": ""}
    m = re.search(r"Ranked from (\d+) ratings?", text)
    if m:
        row["ratings"] = int(m.group(1))
    for m in GAME_URL.finditer(h):
        if m.group(2).lower() not in NOT_GAME_HOSTS:
            row["game_url"] = m.group(1)
            break
    return row


def parse_game_page(h):
    """Fields from a game page's More information table, plus browser play and mentions of AI above it."""
    text = to_text(h)
    i = text.find("More information")
    info = {}
    for line in (text[i:] if i >= 0 else "").split("\n"):
        cells = [c.strip() for c in line.split("\t") if c.strip()]
        if len(cells) >= 2 and cells[0] in INFO_LABELS and cells[0] not in info:
            info[cells[0]] = cells[1]
    desc = text[:i] if i >= 0 else text
    authors = info.get("Authors") or info.get("Author") or ""
    platforms = info.get("Platforms", "")
    disclosure = (info.get("Content", "") + " " + info.get("AI Disclosure", "")).strip()
    if re.search(r"(?i)no generative ai", disclosure):
        content_ai = "no-ai"
    elif re.search(r"\bAI\b|(?i:generative)", disclosure):
        content_ai = "ai"
    else:
        content_ai = "not stated"
    return {"game_title": page_title(h), "platforms": platforms,
            "browser": "HTML5" in platforms or bool(RUN_GAME.search(h)),
            "engine": info.get("Made with", "").split(",")[0].strip(),
            "team_size": len([a for a in authors.split(",") if a.strip()]) if authors else (1 if info else None),
            "content_ai": content_ai, "desc_mentions_ai": bool(AI_WORDS.search(desc)),
            "session": info.get("Average session", ""), "genre": info.get("Genre", ""),
            "desc_words": len(desc.split()), "info_found": bool(info)}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def title_match(rate_title, game_page_title):
    a, b = norm(rate_title), norm(game_page_title)
    return bool(a) and b.startswith(a)


# ---------- statistics ----------

def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def spread(xs):
    """Mean, sample sd, median, min and max, rounded."""
    n = len(xs)
    mean = sum(xs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return {"n": n, "mean": round(mean, 3), "sd": round(sd, 3), "median": round(median(xs), 3),
            "min": min(xs), "max": max(xs)}


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def ranks(xs):
    """Average ranks (ties share the mean rank), 1 = smallest."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def fisher(a, b, c, d):
    """Fisher exact test of [[a, b], [c, d]] (picks yes/no, rest yes/no): (p_greater, p_less, p_two_sided);
    'greater' means the picks have the feature more often than chance."""
    n1, n2, k = a + b, c + d, a + c
    n = n1 + n2
    probs = {x: math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n, k)
             for x in range(max(0, k - n2), min(k, n1) + 1)}
    obs = probs[a]
    greater = sum(v for x, v in probs.items() if x >= a)
    less = sum(v for x, v in probs.items() if x <= a)
    two = sum(v for v in probs.values() if v <= obs * (1 + 1e-7))
    return min(1.0, greater), min(1.0, less), min(1.0, two)


def holm(ps):
    """Holm-adjusted p-values for {name: p}."""
    order = sorted(ps, key=ps.get)
    out, run = {}, 0.0
    for i, name in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[name]))
        out[name] = round(run, 4)
    return out


def perm_better(pick_vals, all_vals, reps=20000, seed=1):
    """One-sided permutation p: how often a random subset of all_vals, as large as pick_vals, has a mean at
    most the picks' mean (lower = better, as with rank percentiles)."""
    k = len(pick_vals)
    obs = sum(pick_vals) / k
    rng = random.Random(seed)
    hits = sum(1 for _ in range(reps) if sum(rng.sample(all_vals, k)) / k <= obs + 1e-12)
    return (hits + 1) / (reps + 1)


def adjustment_check(rows, crit):
    """Checks itch's rating-count adjustment on one criterion: every entry whose score is below its raw score
    implies a median of ratings * (raw / score)^2; if the formula holds these agree (up to 3-decimal rounding)."""
    pts = [(r["ratings"], r["scores"][crit]["score"], r["scores"][crit]["raw"]) for r in rows
           if r.get("ratings") and crit in r["scores"] and r["scores"][crit]["score"] and r["scores"][crit]["raw"]]
    pen = [(n, s, w) for n, s, w in pts if s < w - 1e-9]
    full = [n for n, s, w in pts if s >= w - 1e-9]
    out = {"criterion": crit, "entries": len(pts), "penalized": len(pen),
           "ratings_median_all": median([n for n, _, _ in pts]) if pts else None,
           "min_ratings_unpenalized": min(full) if full else None,
           "max_ratings_penalized": max(n for n, _, _ in pen) if pen else None}
    if pen:
        out["implied_median"] = spread([round(n * (w / s) ** 2, 3) for n, s, w in pen])
        out["mean_points_lost_penalized"] = round(sum(w - s for _, s, w in pen) / len(pen), 3)
    return out


def binary_features(r):
    return {"browser": r["browser"], "ai_disclosed_itch": r["content_ai"] == "ai",
            "no_ai_stated_itch": r["content_ai"] == "no-ai", "desc_mentions_ai": r["desc_mentions_ai"],
            "team_2plus": (r["team_size"] or 1) >= 2}


def counts(values):
    out = {}
    for v in values:
        out[v or "(blank)"] = out.get(v or "(blank)", 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def summarize(rows):
    crits = {}
    for r in rows:
        for c, v in r["scores"].items():
            crits.setdefault(c, []).append(v)
    picked = [c for c, vs in crits.items() if all(v["score"] is None for v in vs)]
    rated = [c for c in crits if c not in picked]
    main = None
    if rated:
        main = next((c for c in rated if c.lower() == "overall"), None) or max(
            rated, key=lambda c: sum(1 for v in crits[c] if v["score"] is not None))
    out = {"entries": len(rows), "entries_with_scores": sum(1 for r in rows if r["scores"]),
           "criteria": {c: {"kind": "hand-picked" if c in picked else "rated", "entries_ranked": len(crits[c])}
                        for c in crits},
           "main_rated_criterion": main}
    ranked = [r for r in rows if main and main in r["scores"] and r["scores"][main]["score"] is not None]
    n_ranked = len(ranked)
    max_rank = max((r["scores"][main]["rank"] for r in ranked), default=0)
    # a couple of unreadable pages are tolerated; a partial read (ranks far past the rows read) is not
    out["main_ranking_complete"] = bool(ranked) and max_rank <= n_ranked * 1.02 + 1

    def pct(r):
        # max_rank guards against a partial read, where ranks run past the entries actually read
        return r["scores"][main]["rank"] / max(n_ranked, max_rank)

    for c in rated:
        vals = [r["scores"][c] for r in rows if c in r["scores"] and r["scores"][c]["score"] is not None]
        by_rank = sorted(vals, key=lambda v: v["rank"])
        out["criteria"][c]["score"] = spread([v["score"] for v in vals]) if vals else None
        out["criteria"][c]["score_at_rank"] = {str(k): by_rank[k - 1]["score"] for k in (1, 3, 5, 10, 30)
                                               if len(by_rank) >= k}
    full = [r for r in rows if all(c in r["scores"] and r["scores"][c]["score"] is not None for c in rated)]
    if len(rated) > 1 and len(full) >= 3:
        out["rated_correlations_spearman"] = {
            "%s ~ %s" % (rated[i], rated[j]): round(spearman([r["scores"][rated[i]]["score"] for r in full],
                                                             [r["scores"][rated[j]]["score"] for r in full]) or 0, 3)
            for i in range(len(rated)) for j in range(i + 1, len(rated))}
    rated_counts = [r["ratings"] for r in rows if r.get("ratings") is not None]
    if rated_counts:
        out["ratings_per_entry"] = spread(rated_counts)
    if main:
        out["adjustment"] = adjustment_check(rows, main)

    picks = [r for r in rows if any(c in r["scores"] for c in picked)]
    in_ranked, in_picks = {id(r) for r in ranked}, {id(r) for r in picks}
    out["picks"] = [{"title": r["title"], "awards": {c: r["scores"][c]["rank"] for c in picked if c in r["scores"]},
                     "main_rank": r["scores"][main]["rank"] if id(r) in in_ranked else None,
                     "main_score": r["scores"][main]["score"] if id(r) in in_ranked else None,
                     "main_raw": r["scores"][main]["raw"] if id(r) in in_ranked else None,
                     "ratings": r.get("ratings"),
                     **{k: r.get(k) for k in ("browser", "engine", "team_size", "content_ai", "desc_mentions_ai",
                                              "session", "platforms")}} for r in picks]
    pick_pcts = [pct(r) for r in picks if id(r) in in_ranked]
    if pick_pcts:
        out["picks_in_main_ranking"] = {
            "picks": len(picks), "picks_ranked": len(pick_pcts), "entries_ranked": n_ranked,
            "median_percentile": round(median(pick_pcts), 3), "mean_percentile": round(sum(pick_pcts) / len(pick_pcts), 3),
            "in_top_10pct": sum(1 for p in pick_pcts if p <= 0.10), "in_top_25pct": sum(1 for p in pick_pcts if p <= 0.25),
            "in_top_50pct": sum(1 for p in pick_pcts if p <= 0.50),
            "perm_p_better_than_random": round(perm_better(pick_pcts, [pct(r) for r in ranked]), 5),
            "note": "descriptive: the picks' community ranks were seen before this test was written"}

    # picks vs the rest of the ranked entries, on game-page features
    have = [r for r in ranked if r.get("info_found")]
    pk = [r for r in have if id(r) in in_picks]
    rest = [r for r in have if id(r) not in in_picks]
    out["game_pages"] = {"ranked_with_info": len(have), "ranked_without_info": len(ranked) - len(have),
                         "title_mismatches": [r["title"] for r in rows if r.get("info_found") and not r.get("title_ok")][:15]}
    if have:
        out["all_ranked"] = {"engine": counts(r["engine"] for r in have), "content_ai": counts(r["content_ai"] for r in have),
                             "session": counts(r["session"] for r in have),
                             "browser": sum(1 for r in have if r["browser"]),
                             "desc_mentions_ai": sum(1 for r in have if r["desc_mentions_ai"]),
                             "team_size": spread([r["team_size"] or 1 for r in have]),
                             "desc_words": spread([r["desc_words"] for r in have])}
    if pk and rest:
        feats = {}
        for f in binary_features(have[0]):
            a = sum(1 for r in pk if binary_features(r)[f])
            c = sum(1 for r in rest if binary_features(r)[f])
            g, l, t = fisher(a, len(pk) - a, c, len(rest) - c)
            feats[f] = {"picks": "%d/%d" % (a, len(pk)), "rest": "%d/%d" % (c, len(rest)),
                        "picks_share": round(a / len(pk), 3), "rest_share": round(c / len(rest), 3),
                        "p_greater": round(g, 4), "p_less": round(l, 4), "p_two_sided": round(t, 4)}
        out["picks_vs_rest"] = feats
        raw_p = {h: feats[f]["p_" + {"less": "less", "greater": "greater", "two": "two_sided"}[d]]
                 for h, (f, d) in PREREGISTERED.items()}
        out["preregistered"] = {"raw_p": raw_p, "holm_p": holm(raw_p)}
        out["picks_engine"] = counts(r["engine"] for r in pk)
        out["picks_session"] = counts(r["session"] for r in pk)
        out["picks_team_size"] = spread([r["team_size"] or 1 for r in pk])
        out["picks_desc_words"] = spread([r["desc_words"] for r in pk])
        pr = [r["ratings"] for r in pk if r.get("ratings") is not None]
        rr = [r["ratings"] for r in rest if r.get("ratings") is not None]
        if pr and rr:
            out["ratings_picks_vs_rest_median"] = [median(pr), median(rr)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jam", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--raw-dir", default="", help="reuse pages saved by an earlier run (no network)")
    ap.add_argument("--no-game-pages", action="store_true")
    a = ap.parse_args()
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    problems = []

    def page(name, url):
        if a.raw_dir:
            p = os.path.join(a.raw_dir, name)
            return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        try:
            h = fetch(url)
        except Exception as e:
            problems.append("%s: %r" % (url, e))
            return ""
        with open(os.path.join(raw, name), "w", encoding="utf-8") as f:
            f.write(h)
        time.sleep(a.delay)
        return h

    path = "/jam/%s/results" % a.jam
    first = page("results-1.html", BASE + path)
    ids = rate_ids(first, a.jam)
    views = [("", first)] + [(s, None) for s in criteria_slugs(first, a.jam)]
    pages_read = {}
    for slug, h in views:
        vpath = path + ("/" + slug if slug else "")
        tag = slug or "main"
        if h is None:
            h = page("results-%s-1.html" % tag, BASE + vpath)
        ids += [i for i in rate_ids(h, a.jam) if i not in ids]
        n_pages = page_count(h, vpath)
        pages_read[tag] = n_pages
        for n in range(2, n_pages + 1):
            hp = page("results-%s-%d.html" % (tag, n), "%s%s?page=%d" % (BASE, vpath, n))
            ids += [i for i in rate_ids(hp, a.jam) if i not in ids]
    print("criteria views %d, pages %s, entries %d" % (len(views), pages_read, len(ids)), flush=True)

    rows = []
    for k, rid in enumerate(ids):
        h = page("rate-%s.html" % rid, "%s/jam/%s/rate/%s" % (BASE, a.jam, rid))
        if not h:
            continue
        row = parse_rate_page(h)
        row["rate_id"] = rid
        if row["game_url"] and not a.no_game_pages:
            g = page("game-%s.html" % rid, row["game_url"])
            if g:
                row.update(parse_game_page(g))
                row["title_ok"] = title_match(row["title"], row["game_title"])
        rows.append(row)
        if k % 25 == 0:
            print("read %d/%d" % (k + 1, len(ids)), flush=True)

    cols = ["rate_id", "title", "ratings", "scores", "browser", "platforms", "engine", "team_size", "content_ai",
            "desc_mentions_ai", "session", "genre", "desc_words", "title_ok"]
    with open(os.path.join(a.out, "entries.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r["scores"], ensure_ascii=False) if c == "scores" else r.get(c, "") for c in cols])
    summary = summarize(rows)
    with_info = sum(1 for r in rows if r.get("info_found"))
    summary.update({"jam": a.jam, "results_pages": pages_read, "problems": problems,
                    "parsed_ok": bool(rows) and summary["entries_with_scores"] >= 0.9 * len(rows)
                    and summary["main_ranking_complete"]
                    and (a.no_game_pages or with_info >= 0.8 * len(rows))})
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: summary.get(k) for k in ("entries", "results_pages", "main_ranking_complete", "criteria",
                                                   "picks_in_main_ranking", "picks_vs_rest", "preregistered",
                                                   "adjustment", "parsed_ok")}, indent=2, ensure_ascii=False))
    sys.exit(0 if summary["parsed_ok"] else 1)


if __name__ == "__main__":
    main()
