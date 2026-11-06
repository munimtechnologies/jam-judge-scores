# Tests for judge_reach.py. By MV2 of Munim, Inc.; made with AI agents (Anthropic Claude). Apache-2.0.
import csv
import json
import os
import tempfile
import unittest

import judge_reach as jr

SLUG = "demo-jam"
ORD = {1: "1st", 2: "2nd", 3: "3rd"}


def entry(rid, title, rank, score, raw, n, extra_rows=""):
    """One entry in itch.io's real results layout (checked against GDevelop jam #1 and #9 pages, 2026-11-06):
    the <h2> links to the game page, the /rate/ link is 'View submission page', the ratings count sits in
    'Ranked 2nd with 68 ratings (Score: 4.062)'."""
    return (
        '<div class="game_rank"><a href="https://a.itch.io/g%s" class="game_cover"><img src="x.png"></a>'
        '<div class="game_summary"><h2><a href="https://a.itch.io/g%s">%s</a></h2>'
        '<h3>by <a href="https://a.itch.io">Someone</a></h3>'
        '<h3>Ranked <strong class="ordinal_rank">%s</strong> with %d ratings (Score: %s)</h3>'
        '<p><a href="/jam/%s/rate/%s" class="forward_link">View submission page</a></p></div>'
        '<table class="nice_table ranking_results_table"><thead><tr><td>Criteria</td><td>Rank</td>'
        '<td>Score*</td><td>Raw Score</td></tr></thead>'
        '<tr><td><a href="/jam/%s/results/overall">Overall</a></td><td>#%d</td><td>%s</td><td>%s</td></tr>%s'
        '</table></div>'
        % (rid, rid, title, ORD.get(rank, "%dth" % rank), n, score, SLUG, rid, SLUG, rank, score, raw, extra_rows))


def old_entry(rid, title, rank, score, raw, n):
    """A layout where the title is the /rate/ link and the count is 'Ranked from N ratings'."""
    return (
        '<div class="game_rank"><div class="game_summary"><h2><a href="/jam/%s/rate/%s">%s</a></h2></div>'
        '<table><tr><td>Overall</td><td>#%d</td><td>%s</td><td>%s</td></tr></table>'
        '<p>Ranked from %d ratings.</p></div>' % (SLUG, rid, title, rank, score, raw, n))


PAGE1 = ('<html><body><p>7,025 ratings were given to 401 entries (100.0%) by 300 people.</p>'
         '<div class="game_ranking responsive_column">'
         + entry(11, "Cheese The Skies", 1, "4.316", "4.316", 19)
         + entry(12, "Illegal Fat Gambling (DEMO)", 2, "4.062", "4.062", 68,
                 '<tr><td><a href="/jam/demo-jam/results/fun">Fun &amp; Game Design</a></td>'
                 '<td>#5</td><td>4.1</td><td>4.1</td></tr>')
         + '<a href="?page=2">Next</a></div></body></html>')
PAGE2 = ('<html><body>' + entry(13, "Kilimanjaro (Game Jam Submission)", 3, "3.688", "3.688", 43)
         + entry(14, "Northburg: GameJam Edition", 4, "3.1", "3.5", 1)
         + entry(15, "Tom &amp; Jerry", 5, "3.0", "3.0", 9) + '</body></html>')


class Parse(unittest.TestCase):
    def test_page(self):
        es = jr.parse_page(PAGE1, SLUG)
        self.assertEqual([e["rate_id"] for e in es], ["11", "12"])
        self.assertEqual(es[0]["title"], "Cheese The Skies")
        self.assertEqual(es[1]["title"], "Illegal Fat Gambling (DEMO)")
        self.assertEqual((es[1]["rank"], es[1]["score"], es[1]["raw"], es[1]["ratings"]), (2, 4.062, 4.062, 68))
        self.assertEqual(es[1]["criterion"], "Overall")
        self.assertEqual(es[1]["headline_rank"], 2)
        self.assertEqual(jr.page_count(PAGE1), 2)

    def test_never_takes_link_label_as_title(self):
        # 0.2.1: a real title may itself contain the word "Submission" ("Kilimanjaro (Game Jam Submission)",
        # GDevelop jam #9), so the check is that the title is never one of the link labels, not a substring test.
        titles = []
        for e in jr.parse_page(PAGE1, SLUG) + jr.parse_page(PAGE2, SLUG):
            self.assertNotIn(e["title"].lower(), jr.NOT_TITLES)
            self.assertTrue(e["title"])
            self.assertIsNotNone(e["ratings"])
            titles.append(e["title"])
        self.assertIn("Kilimanjaro (Game Jam Submission)", titles)

    def test_old_layout_still_parses(self):
        h = old_entry(21, "Soul Out", 7, "3.2", "3.2", 12) + old_entry(22, "Logica", 8, "3.1", "3.1", 30)
        es = jr.parse_page(h, SLUG)
        self.assertEqual([(e["title"], e["rank"], e["ratings"]) for e in es],
                         [("Soul Out", 7, 12), ("Logica", 8, 30)])

    def test_headline_only(self):
        h = ('<div class="game_rank"><h2><a href="https://b.itch.io/x">Avast!</a></h2>'
             '<h3>Ranked <strong class="ordinal_rank">12th</strong> with 7 ratings (Score: 3.5)</h3>'
             '<a href="/jam/demo-jam/rate/31">View submission page</a></div>')
        e = jr.parse_page(h, SLUG)[0]
        self.assertEqual((e["title"], e["rank"], e["ratings"], e["criterion"]), ("Avast!", 12, 7, "headline"))

    def test_adjustment_effect(self):
        es = [{"rate_id": "a", "rank": 1, "raw": 4.0, "ratings": 20},
              {"rate_id": "b", "rank": 2, "raw": 3.9, "ratings": 25},
              {"rate_id": "c", "rank": 3, "raw": 4.5, "ratings": 2}]
        self.assertEqual(jr.raw_ranks(es), {"a": 2, "b": 3, "c": 1})
        self.assertEqual(jr.adjustment_effect(es, top=2),
                         {"raw_top_displaced": 1, "displaced_max_ratings": 2, "min_ratings_top": 20})

    def test_match(self):
        es = jr.parse_page(PAGE1, SLUG) + jr.parse_page(PAGE2, SLUG)
        e, kind, _ = jr.match("Kilimanjaro", es)
        self.assertEqual((e["rank"], kind), (3, "prefix"))
        e, kind, _ = jr.match("Illegal Fat Gambling", es)
        self.assertEqual((e["rank"], kind), (2, "prefix"))
        e, kind, _ = jr.match("Northburg", es)
        self.assertEqual((e["rank"], kind), (4, "prefix"))
        e, kind, _ = jr.match("cheese the skies", es)
        self.assertEqual(kind, "exact")
        e, kind, _ = jr.match("Tom and Jerry", es)
        self.assertEqual(kind, "exact")
        e, kind, c = jr.match("Something Else Entirely", es)
        self.assertIsNone(e)
        self.assertEqual(kind, "none")

    def test_main_from_raw(self):
        with tempfile.TemporaryDirectory() as d:
            raw = os.path.join(d, "raw-in", SLUG)
            os.makedirs(raw)
            for name, page in (("results-1.html", PAGE1), ("results-2.html", PAGE2)):
                with open(os.path.join(raw, name), "w", encoding="utf-8") as f:
                    f.write(page)
            picks = os.path.join(d, "picks.csv")
            with open(picks, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["jam", "slug_candidates", "place", "title", "blog_url"])
                w.writerow([9, "missing-jam|" + SLUG, 1, "Illegal Fat Gambling", "u"])
                w.writerow([9, "missing-jam|" + SLUG, 2, "Kilimanjaro", "u"])
                w.writerow([9, "missing-jam|" + SLUG, 3, "Not There", "u"])
            out = os.path.join(d, "out")
            jr.main(["--picks", picks, "--out", out, "--from-raw", os.path.join(d, "raw-in"), "--delay", "0"])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual((s["picks"], s["found"], s["ranks_sorted"]), (3, 2, [2, 3]))
            self.assertEqual(s["in_top_10"], 2)
            self.assertEqual(s["fewest_ratings"], 43)
            with open(os.path.join(out, "picks.csv"), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[1]["ranked_in_jam"], "5")
            self.assertEqual(rows[1]["rank_pct"], "60.0")
            self.assertEqual(rows[1]["ratings"], "43")
            self.assertEqual(rows[2]["match"], "none")
            self.assertEqual((rows[0]["raw_rank"], rows[1]["raw_rank"]), ("2", "3"))
            self.assertEqual(s["picks_ranked_lower_than_raw"], 0)
            self.assertEqual(s["raw_ranks_sorted"], [2, 3])
            with open(os.path.join(out, "jams.csv"), encoding="utf-8") as f:
                jams = list(csv.DictReader(f))
            self.assertEqual(jams[0]["slug"], SLUG)
            self.assertIn("7,025 ratings were given", jams[0]["stats_text"])
            self.assertEqual(jams[0]["median_ratings_ranked"], "19")
            self.assertEqual((jams[0]["missing_title"], jams[0]["headline_mismatch"]), ("0", "0"))
            self.assertEqual((jams[0]["raw_top_displaced"], jams[0]["min_ratings_top"]), ("0", "1"))
            # author names never reach the entries file
            with open(os.path.join(out, "entries", SLUG + ".csv"), encoding="utf-8") as f:
                text = f.read()
            self.assertNotIn("Someone", text)


if __name__ == "__main__":
    unittest.main()
