"""Results census of one itch.io jam: every ranked entry's criteria scores, rating count and submission-form
answers (Apache-2.0). By MV2 of Munim, Inc., made with AI agents (Anthropic Claude).

    python jam_census.py --jam slapjam-ai-1 --out /out [--delay 1.5] [--raw-dir DIR]

Reads only public pages that itch.io's robots.txt allows (/jam/<jam>/results and /jam/<jam>/rate/<id>), one
request every --delay seconds, with a User-Agent that names MV2 and his email. Saves every page it read under
out/raw/ so the parse can be redone offline (--raw-dir reuses them without any network). Writes entries.csv
(one row per entry; author handles are kept out of the CSV and summary) and summary.json (criteria
correlations, the form answers and mean scores by answer).

0.2.0: form answers come only from the entry's field_responses block (0.1.0 also caught question-like lines
from comments) and keep every ticked box (0.1.0 kept the first); pages without scores are not entries;
the summary adds per-criterion spread, an equal-weight overall ranking and the score needed for the top 5.
"""
import argparse
import csv
import html
import json
import math
import os
import re
import sys
import time
import urllib.request

BASE = "https://itch.io"
UA = "MV2-Munim-jam-census/0.2 (MV2 of Munim, Inc.; mv2@munimtech.com)"
CRITERIA = ["Fun", "Visual Appeal", "Theme Following"]


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


def rate_ids(page_html, jam):
    """Entry ids linked from a results page, in page order, without repeats."""
    return list(dict.fromkeys(re.findall(r"/jam/%s/rate/(\d+)" % re.escape(jam), page_html)))


def page_count(page_html):
    nums = [int(n) for n in re.findall(r"[?&]page=(\d+)", page_html)]
    return max(nums) if nums else 1


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


def game_title(page_title):
    """'Game by author for Jam - itch.io' -> 'Game' (author handles stay out of the data)."""
    m = re.match(r"(.*) by .+? for .+ - itch\.io$", page_title)
    if m:
        return m.group(1)
    return re.sub(r"\s*-\s*itch\.io$", "", page_title)


SCORE_ROW = re.compile(r"(%s)\s*\t?\s*#(\d+)\s+([\d.]+)\s+([\d.]+)" % "|".join(CRITERIA))
FIELDS = re.compile(r'(?is)class="field_responses">(.*?)(?:</section>|$)')
BADGE = re.compile(r'(?is)class="badge_summary">\s*<strong>(.*?)</strong>')


def form_answers(page_html):
    """Submission-form answers from the entry's own field_responses block (comments below it stay out).
    A ticked-boxes answer is every badge name joined by ', '; a text answer is its text on one line."""
    m = FIELDS.search(page_html)
    if not m:
        return {}
    out = {}
    for block in re.findall(r"(?is)<p>(.*?)</p>", m.group(1)):
        q = re.match(r"(?is)\s*<strong>(.*?)</strong>(.*)", block)
        if not q:
            continue
        question = " ".join(to_text(q.group(1)).split())
        badges = [" ".join(to_text(b).split()) for b in BADGE.findall(q.group(2))]
        answer = ", ".join(b for b in badges if b) if badges else " ".join(to_text(q.group(2)).split())
        if question and answer:
            out[question] = answer[:400]
    return out


def parse_rate_page(page_html):
    text = to_text(page_html)
    row = {"title": "", "ratings": None, "answers": form_answers(page_html)}
    m = re.search(r"(?is)<title>(.*?)</title>", page_html)
    if m:
        row["title"] = game_title(html.unescape(re.sub(r"\s+", " ", m.group(1))).strip())
    for name, rank, score, raw in SCORE_ROW.findall(text):
        key = name.lower().replace(" ", "_")
        row[key + "_rank"], row[key + "_score"], row[key + "_raw"] = int(rank), float(score), float(raw)
    m = re.search(r"Ranked from (\d+) ratings?", text)
    if m:
        row["ratings"] = int(m.group(1))
    return row


def split_answer(a):
    return [p.strip() for p in re.split(r",\s*|\s*\t\s*", a) if p.strip()]


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


def spread(xs):
    """Mean, sample sd, median, min and max, rounded."""
    n = len(xs)
    s = sorted(xs)
    mean = sum(xs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"mean": round(mean, 3), "sd": round(sd, 3), "median": round(med, 3), "min": s[0], "max": s[-1]}


def summarize(rows):
    keys = [c.lower().replace(" ", "_") + "_score" for c in CRITERIA]
    full = [r for r in rows if all(k in r for k in keys)]
    out = {"pages_read": len(rows), "entries": len(full), "entries_with_all_scores": len(full),
           "pages_without_scores": [r["title"] for r in rows if r not in full], "correlations": {}}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            xs, ys = [r[keys[i]] for r in full], [r[keys[j]] for r in full]
            out["correlations"]["%s~%s" % (keys[i], keys[j])] = {
                "pearson": round(pearson(xs, ys), 3) if pearson(xs, ys) is not None else None,
                "spearman": round(spearman(xs, ys), 3) if spearman(xs, ys) is not None else None}
    if full:
        out["criteria"] = {k: spread([r[k] for r in full]) for k in keys}
        for r in full:
            r["overall"] = sum(r[k] for k in keys) / len(keys)
        by_overall = sorted(full, key=lambda r: -r["overall"])
        out["overall_equal_weight"] = spread([r["overall"] for r in full])
        out["overall_needed"] = {"rank_1": round(by_overall[0]["overall"], 3),
                                 "rank_5": round(by_overall[min(4, len(full) - 1)]["overall"], 3),
                                 "rank_10": round(by_overall[min(9, len(full) - 1)]["overall"], 3)}
        out["top10_overall"] = [{"title": r["title"], "overall": round(r["overall"], 3),
                                 **{k: r[k] for k in keys}, "ratings": r.get("ratings")} for r in by_overall[:10]]
    rated = [r for r in full if r.get("ratings") is not None]
    if rated:
        out["ratings_per_entry"] = {"min": min(r["ratings"] for r in rated), "max": max(r["ratings"] for r in rated),
                                    "mean": round(sum(r["ratings"] for r in rated) / len(rated), 2)}
        xs, ys = [r["ratings"] for r in rated], [r[keys[0]] for r in rated]
        s = spearman(xs, ys)
        out["ratings_vs_fun_spearman"] = round(s, 3) if s is not None else None
    # every form question, how often each answer part appears, and the mean scores with and without it
    questions = {}
    for r in full:
        for q, a in r["answers"].items():
            questions.setdefault(q, {})
            for part in split_answer(a):
                questions[q].setdefault(part, []).append(r)
    out["answers"] = {}
    for q, parts in questions.items():
        answered = {id(r) for rs in parts.values() for r in rs}
        if len(answered) < 5:  # a page label, not a form question
            continue
        out["answers"][q] = {"entries_answering": len(answered), "parts": {}}
        for part, rs in sorted(parts.items(), key=lambda kv: -len(kv[1])):
            if len(rs) < 3:
                continue
            ids = {id(r) for r in rs}
            others = [r for r in full if id(r) not in ids]
            out["answers"][q]["parts"][part] = {
                "entries": len(rs),
                "mean_with": {k: round(sum(r[k] for r in rs) / len(rs), 3) for k in keys},
                "mean_without": {k: round(sum(r[k] for r in others) / len(others), 3) if others else None for k in keys}}
        # answers that tick several boxes, and those that tick "None of these" together with a tool
        multi = [r for r in full if len(split_answer(r["answers"].get(q, ""))) > 1]
        out["answers"][q]["entries_ticking_several"] = len(multi)
        out["answers"][q]["entries_ticking_none_and_a_tool"] = sum(
            1 for r in multi if "None of these" in split_answer(r["answers"][q]))
    top = sorted(full, key=lambda r: r.get("fun_rank", 10**6))[:10]
    out["top10_by_fun"] = [{"title": r["title"], **{k: r[k] for k in keys}, "ratings": r.get("ratings"),
                            "answers": r["answers"]} for r in top]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jam", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--raw-dir", default="", help="reuse pages saved by an earlier run (no network)")
    a = ap.parse_args()
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    problems = []

    def page(name, url):
        if a.raw_dir:
            p = os.path.join(a.raw_dir, name)
            return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        h = fetch(url)
        with open(os.path.join(raw, name), "w", encoding="utf-8") as f:
            f.write(h)
        time.sleep(a.delay)
        return h

    first = page("results-1.html", "%s/jam/%s/results" % (BASE, a.jam))
    pages = page_count(first)
    ids = rate_ids(first, a.jam)
    for n in range(2, pages + 1):
        ids += [i for i in rate_ids(page("results-%d.html" % n, "%s/jam/%s/results?page=%d" % (BASE, a.jam, n)), a.jam)
                if i not in ids]
    print("results pages %d, entries %d" % (pages, len(ids)), flush=True)
    rows = []
    for k, rid in enumerate(ids):
        try:
            h = page("rate-%s.html" % rid, "%s/jam/%s/rate/%s" % (BASE, a.jam, rid))
        except Exception as e:
            problems.append("rate %s: %r" % (rid, e))
            continue
        row = parse_rate_page(h)
        row["rate_id"] = rid
        rows.append(row)
        if k % 20 == 0:
            print("read %d/%d" % (k + 1, len(ids)), flush=True)

    cols = ["rate_id", "title", "ratings"] + [c.lower().replace(" ", "_") + s for c in CRITERIA
                                              for s in ("_rank", "_score", "_raw")] + ["answers"]
    with open(os.path.join(a.out, "entries.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r["answers"], ensure_ascii=False) if c == "answers" else r.get(c, "") for c in cols])
    summary = summarize(rows)
    summary.update({"jam": a.jam, "results_pages": pages, "problems": problems,
                    "parsed_ok": bool(rows) and summary["entries_with_all_scores"] >= 0.9 * len(rows)})
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: summary.get(k) for k in ("entries", "pages_without_scores", "correlations", "criteria",
                                                   "overall_needed", "parsed_ok")}, indent=2, ensure_ascii=False))
    sys.exit(0 if summary["parsed_ok"] else 1)


if __name__ == "__main__":
    main()
