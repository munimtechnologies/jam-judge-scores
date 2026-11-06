# judge_reach.py: where in the community ranking did GDevelop game jam judges find their cash winners?
# Reads the public itch.io results pages of GDevelop jams #1-#9 and finds each Judges' Award winner
# (titles taken by hand from GDevelop's own winner posts, see judge_picks.csv) in the jam's overall
# community ranking, with its number of ratings.
#
# By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents (Anthropic Claude) working in his
# name. Apache-2.0.
#
#   python judge_reach.py --picks judge_picks.csv --out OUT [--from-raw RAWDIR] [--delay 1.5]
#
# Writes OUT/picks.csv (one row per judges' winner), OUT/jams.csv (one row per jam), OUT/summary.json,
# OUT/entries/<slug>.csv (rank, title, ratings, scores; no author names) and OUT/raw/<slug>/*.html.
#
# 0.2 (2026-11-06): itch.io results pages put the game title in the <h2> link (to the game page, not to
# the /rate/ page) and the ratings count in "Ranked 2nd with 68 ratings (Score: 4.062)". 0.1 took the
# "View submission page" link text as the title and found no ratings count, so it matched 0 of 45 picks.

import argparse
import csv
import difflib
import html
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE = "https://itch.io"
UA = "MV2-Munim-judge-reach/0.2 (MV2 of Munim, Inc.; mv2@munimtech.com)"


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, ""
            last = e
        except Exception as e:
            last = e
        time.sleep(5 * (i + 1))
    raise last


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


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


def page_count(page_html):
    nums = [int(n) for n in re.findall(r"[?&](?:amp;)?page=(\d+)", page_html)]
    return max(nums) if nums else 1


ROW = re.compile(r"(?m)^\s*([^\t\n#]{1,60}?)\s*\t\s*#(\d+)\s*\t\s*([\d.]+)\s*\t\s*([\d.]+)")
NOT_TITLES = {"view submission page", "rate this game", ""}


def blocks(page_html, slug):
    """Split a results page into one HTML chunk per ranked entry, in page order."""
    link = re.compile(r'href="(?:https?://itch\.io)?/jam/%s/rate/(\d+)"' % re.escape(slug))
    if 'class="game_rank' in page_html:
        parts = re.split(r'<div class="game_rank', page_html)[1:]
        return [p for p in parts if link.search(p)]
    seen, starts = set(), []
    for m in link.finditer(page_html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            starts.append(m.start())
    return [page_html[a:b] for a, b in zip(starts, starts[1:] + [len(page_html)])]


def block_title(chunk, slug, rid):
    """The entry's title: the <h2> text (itch.io's layout), else a /rate/ link text that is a real title."""
    m = re.search(r"(?is)<h2\b[^>]*>(.*?)</h2>", chunk)
    if m:
        t = " ".join(to_text(m.group(1)).split())
        if t.lower() not in NOT_TITLES:
            return t
    for m in re.finditer(r'(?is)<a\b[^>]*href="(?:https?://itch\.io)?/jam/%s/rate/%s"[^>]*>(.*?)</a>'
                         % (re.escape(slug), rid), chunk):
        t = " ".join(to_text(m.group(1)).split())
        if t.lower() not in NOT_TITLES:
            return t
    return ""


def parse_block(chunk, slug):
    rid = re.search(r"/jam/%s/rate/(\d+)" % re.escape(slug), chunk).group(1)
    title = block_title(chunk, slug, rid)
    text = to_text(chunk)
    rows = ROW.findall(text)
    crit = rank = score = raw = None
    for name, r, s, w in rows:
        if name.strip().lower() == "overall":
            crit, rank, score, raw = "Overall", int(r), float(s), float(w)
            break
    if rank is None and rows:
        name, r, s, w = rows[0]
        crit, rank, score, raw = name.strip(), int(r), float(s), float(w)
    head = re.search(r"Ranked (\d+)(?:st|nd|rd|th) with (\d+) ratings?(?: \(Score: ([\d.]+)\))?", text)
    if rank is None and head:
        crit, rank = "headline", int(head.group(1))
        score = float(head.group(3)) if head.group(3) else None
    m = re.search(r"Ranked from (\d+) ratings?", text)
    ratings = int(head.group(2)) if head else (int(m.group(1)) if m else None)
    return {"rate_id": rid, "title": title, "criterion": crit, "rank": rank, "score": score, "raw": raw,
            "ratings": ratings, "headline_rank": int(head.group(1)) if head else None}


def parse_page(page_html, slug):
    return [parse_block(c, slug) for c in blocks(page_html, slug)]


def norm(s):
    s = html.unescape(s or "").lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", s)


def match(pick, entries):
    """Return (entry or None, kind, candidates). kind: exact, prefix, ambiguous, none."""
    p = norm(pick)
    exact = [e for e in entries if norm(e["title"]) == p]
    if len(exact) == 1:
        return exact[0], "exact", []
    if len(exact) > 1:
        return None, "ambiguous", [e["title"] for e in exact]
    pre = [e for e in entries if len(p) >= 4 and len(norm(e["title"])) >= 4
           and (norm(e["title"]).startswith(p) or p.startswith(norm(e["title"])))]
    if len(pre) == 1:
        return pre[0], "prefix", []
    if len(pre) > 1:
        return None, "ambiguous", [e["title"] for e in pre]
    names = [e["title"] for e in entries]
    return None, "none", difflib.get_close_matches(pick, names, n=3, cutoff=0.4)


def raw_ranks(entries):
    """rate_id -> rank by raw (unadjusted) Overall score: 1 + number of entries with a strictly higher raw score."""
    raws = [e["raw"] for e in entries if e["raw"] is not None]
    return {e["rate_id"]: 1 + sum(1 for r in raws if r > e["raw"]) for e in entries if e["raw"] is not None}


def adjustment_effect(entries, top=10):
    """How itch.io's few-ratings adjustment changed the top of one jam's Overall ranking."""
    rr = raw_ranks(entries)
    raw_top = [e for e in entries if rr.get(e["rate_id"], top + 1) <= top]
    displaced = [e for e in raw_top if e["rank"] is not None and e["rank"] > top]
    adj_top = [e for e in entries if e["rank"] is not None and e["rank"] <= top]
    counts = [e["ratings"] for e in adj_top if e["ratings"] is not None]
    return {"raw_top_displaced": len(displaced),
            "displaced_max_ratings": max((e["ratings"] for e in displaced if e["ratings"] is not None), default=""),
            "min_ratings_top": min(counts) if counts else ""}


def read_jam(slug, out, from_raw, delay):
    """All ranked entries of one jam (None if the jam has no results page)."""
    rawdir = os.path.join(out, "raw", slug)
    os.makedirs(rawdir, exist_ok=True)

    def page(n):
        name = "results-%d.html" % n
        if from_raw:
            p = os.path.join(from_raw, slug, name)
            return (200, read_text(p)) if os.path.exists(p) else (404, "")
        url = "%s/jam/%s/results" % (BASE, slug) + ("?page=%d" % n if n > 1 else "")
        status, h = fetch(url)
        if status == 200:
            with open(os.path.join(rawdir, name), "w", encoding="utf-8") as f:
                f.write(h)
        time.sleep(delay)
        return status, h

    status, first = page(1)
    if status != 200 or "/jam/%s/rate/" % slug not in first:
        return None
    pages = page_count(first)
    entries = parse_page(first, slug)
    stats = re.search(r"[\d,]+ ratings? (?:were|was) given[^\n<]{0,200}", to_text(first))
    for n in range(2, pages + 1):
        status, h = page(n)
        if status != 200:
            print("  %s page %d: HTTP %s" % (slug, n, status), flush=True)
            continue
        ids = {e["rate_id"] for e in entries}
        entries += [e for e in parse_page(h, slug) if e["rate_id"] not in ids]
    return {"slug": slug, "pages": pages, "entries": entries, "stats_text": stats.group(0) if stats else ""}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--from-raw", default="")
    ap.add_argument("--delay", type=float, default=1.5)
    a = ap.parse_args(argv)
    os.makedirs(os.path.join(a.out, "entries"), exist_ok=True)
    with open(a.picks, encoding="utf-8") as f:
        picks = list(csv.DictReader(f))
    jams = {}
    for p in picks:
        jams.setdefault(int(p["jam"]), p["slug_candidates"].split("|"))

    jam_rows, pick_rows, read = [], [], {}
    for jam in sorted(jams):
        got = None
        for slug in jams[jam]:
            print("jam #%d: trying %s" % (jam, slug), flush=True)
            got = read_jam(slug, a.out, a.from_raw, a.delay)
            if got:
                break
        if not got:
            print("jam #%d: no results page found" % jam, flush=True)
            jam_rows.append({"jam": jam, "slug": "", "pages": 0, "ranked": 0})
            continue
        es = got["entries"]
        read[jam] = got
        with open(os.path.join(a.out, "entries", got["slug"] + ".csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["rank", "title", "ratings", "score", "raw", "criterion", "rate_id"])
            w.writeheader()
            for e in es:
                w.writerow({k: e[k] for k in w.fieldnames})
        counts = [e["ratings"] for e in es if e["ratings"] is not None]
        ranks = [e["rank"] for e in es if e["rank"] is not None]
        jam_rows.append({"jam": jam, "slug": got["slug"], "pages": got["pages"], "ranked": len(es),
                         **adjustment_effect(es),
                         "max_rank": max(ranks) if ranks else "", "criterion": es[0]["criterion"] if es else "",
                         "median_ratings_ranked": statistics.median(counts) if counts else "",
                         "missing_rank": sum(1 for e in es if e["rank"] is None),
                         "missing_ratings": sum(1 for e in es if e["ratings"] is None),
                         "missing_title": sum(1 for e in es if not e["title"]),
                         "headline_mismatch": sum(1 for e in es if e["headline_rank"] is not None
                                                  and e["rank"] is not None and e["headline_rank"] != e["rank"]),
                         "stats_text": got["stats_text"]})
        print("jam #%d: %s, %d pages, %d ranked entries" % (jam, got["slug"], got["pages"], len(es)), flush=True)

    for p in picks:
        jam = int(p["jam"])
        got = read.get(jam)
        row = {"jam": jam, "place": int(p["place"]), "title": p["title"], "matched_title": "", "match": "no_jam",
               "rank": "", "ratings": "", "score": "", "raw": "", "ranked_in_jam": "", "rank_pct": "",
               "median_ratings_ranked": "", "raw_rank": "", "candidates": ""}
        if got:
            es = got["entries"]
            e, kind, cands = match(p["title"], es)
            if e:
                row["raw_rank"] = raw_ranks(es).get(e["rate_id"], "")
            row["match"], row["candidates"] = kind, " | ".join(cands)
            row["ranked_in_jam"] = len(es)
            counts = [x["ratings"] for x in es if x["ratings"] is not None]
            row["median_ratings_ranked"] = statistics.median(counts) if counts else ""
            if e:
                row.update({"matched_title": e["title"], "rank": e["rank"], "ratings": e["ratings"],
                            "score": e["score"], "raw": e["raw"]})
                if e["rank"]:
                    row["rank_pct"] = round(100.0 * e["rank"] / len(es), 1)
        pick_rows.append(row)

    with open(os.path.join(a.out, "picks.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pick_rows[0].keys()))
        w.writeheader()
        w.writerows(pick_rows)
    with open(os.path.join(a.out, "jams.csv"), "w", newline="", encoding="utf-8") as f:
        keys = ["jam", "slug", "pages", "ranked", "max_rank", "criterion", "median_ratings_ranked",
                "raw_top_displaced", "displaced_max_ratings", "min_ratings_top",
                "missing_rank", "missing_ratings", "missing_title", "headline_mismatch", "stats_text"]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in jam_rows:
            w.writerow({k: r.get(k, "") for k in keys})

    found = [r for r in pick_rows if r["rank"] != ""]
    rk = sorted(int(r["rank"]) for r in found)
    summary = {
        "picks": len(pick_rows), "found": len(found),
        "unmatched": [(r["jam"], r["title"], r["match"], r["candidates"]) for r in pick_rows if r["rank"] == ""],
        "ranks_sorted": rk,
        "in_top_5": sum(1 for x in rk if x <= 5), "in_top_10": sum(1 for x in rk if x <= 10),
        "in_top_20": sum(1 for x in rk if x <= 20), "in_top_30": sum(1 for x in rk if x <= 30),
        "worst_rank": max(rk) if rk else None,
        "median_rank": statistics.median(rk) if rk else None,
        "fewest_ratings": min((int(r["ratings"]) for r in found if r["ratings"] != ""), default=None),
        "picks_below_jam_median_ratings": sum(1 for r in found if r["ratings"] != "" and r["median_ratings_ranked"] != ""
                                              and float(r["ratings"]) < float(r["median_ratings_ranked"])),
        "rank_pct_sorted": sorted(float(r["rank_pct"]) for r in found if r["rank_pct"] != ""),
        "picks_ranked_lower_than_raw": sum(1 for r in found if r["raw_rank"] != "" and int(r["rank"]) > int(r["raw_rank"])),
        "raw_ranks_sorted": sorted(int(r["raw_rank"]) for r in found if r["raw_rank"] != ""),
        "jams_raw_top10_displaced": [(r["jam"], r.get("raw_top_displaced", "")) for r in jam_rows],
    }
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    for r in pick_rows:
        print("#%s pick %s: %s -> %s rank %s of %s, %s ratings (jam median %s) [%s] %s" % (
            r["jam"], r["place"], r["title"], r["matched_title"], r["rank"], r["ranked_in_jam"], r["ratings"],
            r["median_ratings_ranked"], r["match"], r["candidates"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
