"""Tests for jam_picks.py (Apache-2.0). By MV2 of Munim, Inc., made with AI agents (Anthropic Claude)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jam_picks as jp  # noqa: E402

RATE = """<html><head><title>Sky Song by someone for Test Jam - itch.io</title>
<link href="https://static.itch.io/main.css" rel="stylesheet"/></head><body>
<div class="jam_header"><a href="https://host.itch.io">Host</a> <a href="https://static.itch.io/logo">x</a></div>
<a class="button" href="https://someone.itch.io/sky-song">View game page</a>
<h2>Results</h2>
<table><tr><th>Criteria</th><th>Rank</th><th>Score*</th><th>Raw Score</th></tr>
<tr><td><a href="/jam/test-jam/results">Best Overall</a></td><td>#1</td><td>n/a</td><td>n/a</td></tr>
<tr><td><a href="/jam/test-jam/results/communitys-voice">Community&#x27;s Voice</a></td><td>#12</td><td>3.900</td>
<td>4.100</td></tr></table>
<p>Ranked from 9 ratings. Score is adjusted from raw score by the median number of ratings per game in the jam.</p>
<div class="comment"><p>#3 4.5 4.0 nice game</p></div></body></html>"""

GAME = """<html><head><title>Sky Song by someone</title>
<style>.game_frame{background:#e5e5e5}</style></head><body>
<div class="formatted_description"><p>A calm flying game. Music made with Suno AI.</p></div>
<div data-iframe="x" class="iframe_placeholder"><button class="button load_iframe_btn">Run game</button></div>
<div class="toggle"><a>More information</a></div>
<div class="info"><table>
<tr><td>Status</td><td>Released</td></tr>
<tr><td>Platforms</td><td><a>HTML5</a>, <a>Windows</a></td></tr>
<tr><td>Authors</td><td><a>someone</a>, <a>friend</a></td></tr>
<tr><td>Made with</td><td><a>Godot</a></td></tr>
<tr><td>Content</td><td>No generative AI was used</td></tr>
<tr><td>Average session</td><td>About a half-hour</td></tr>
</table></div><p>Status\tlater junk</p></body></html>"""

# a download-only game page: itch's CSS still mentions .game_frame, which 0.1.0 took for an embed
DOWNLOAD_ONLY = (GAME.replace('<div data-iframe="x" class="iframe_placeholder"><button class="button load_iframe_btn">'
                              'Run game</button></div>', "")
                 .replace("<a>HTML5</a>, ", ""))

# itch's pager on page 1 of a results view (relative links)
PAGER = ('<div class="pager"><a href="?page=2" class="next_page button">Next</a>'
         '<span class="pager_label">Page 1 of <a href="?page=13">13</a></span></div>')


def row(title, scores, ratings=10, **feat):
    r = {"title": title, "ratings": ratings, "scores": scores, "game_url": "x", "info_found": True, "title_ok": True,
         "browser": True, "engine": "Godot", "team_size": 1, "content_ai": "not stated", "desc_mentions_ai": False,
         "session": "", "platforms": "HTML5", "desc_words": 50}
    r.update(feat)
    return r


class ParseTests(unittest.TestCase):
    def test_rate_page(self):
        r = jp.parse_rate_page(RATE)
        self.assertEqual(r["title"], "Sky Song")
        self.assertEqual(r["ratings"], 9)
        self.assertEqual(r["game_url"], "https://someone.itch.io/sky-song")
        self.assertEqual(r["scores"]["Best Overall"], {"rank": 1, "score": None, "raw": None})
        self.assertEqual(r["scores"]["Community's Voice"], {"rank": 12, "score": 3.9, "raw": 4.1})
        self.assertEqual(len(r["scores"]), 2)  # the comment's "#3 4.5 4.0" is not a score row

    def test_no_table(self):
        self.assertEqual(jp.score_rows("Just a page\n#3 4.5 4.0"), {})

    def test_game_page(self):
        g = jp.parse_game_page(GAME)
        self.assertTrue(g["info_found"])
        self.assertEqual(g["platforms"], "HTML5, Windows")
        self.assertTrue(g["browser"])
        self.assertEqual(g["engine"], "Godot")
        self.assertEqual(g["team_size"], 2)
        self.assertEqual(g["content_ai"], "no-ai")
        self.assertTrue(g["desc_mentions_ai"])
        self.assertEqual(g["session"], "About a half-hour")
        self.assertTrue(jp.title_match("Sky Song", g["game_title"]))
        self.assertFalse(jp.title_match("Other", g["game_title"]))

    def test_download_only_is_not_browser(self):
        g = jp.parse_game_page(DOWNLOAD_ONLY)
        self.assertEqual(g["platforms"], "Windows")
        self.assertFalse(g["browser"])
        # an embed without HTML5 in Platforms still counts
        self.assertTrue(jp.parse_game_page(DOWNLOAD_ONLY.replace(
            "<body>", '<body><div class="html_embed_widget" id="html_embed_9446258"></div>'))["browser"])

    def test_game_page_ai_and_missing(self):
        g = jp.parse_game_page(GAME.replace("No generative AI was used", "AI Generated Graphics"))
        self.assertEqual(g["content_ai"], "ai")
        g = jp.parse_game_page(GAME.replace("<tr><td>Content</td><td>No generative AI was used</td></tr>", "")
                               .replace("Suno AI", "a synth").replace("iframe_placeholder", "x")
                               .replace("load_iframe_btn", "y")
                               .replace("<a>HTML5</a>, ", "").replace("<tr><td>Authors</td>", "<tr><td>Nope</td>"))
        self.assertEqual(g["content_ai"], "not stated")
        self.assertFalse(g["desc_mentions_ai"])
        self.assertFalse(g["browser"])
        self.assertEqual(g["team_size"], 1)
        self.assertFalse(jp.parse_game_page("<p>empty</p>")["info_found"])
        self.assertIsNone(jp.parse_game_page("<p>empty</p>")["team_size"])

    def test_ai_words(self):
        for s in ("uses AI art", "A.I. voices", "made with ChatGPT", "generative AI music"):
            self.assertTrue(jp.AI_WORDS.search(s), s)
        for s in ("the MAIN hall", "AIR balloon", "generative art", "said goodbye"):
            self.assertFalse(jp.AI_WORDS.search(s), s)

    def test_results_links(self):
        h = ('<a href="/jam/j1/results/best-gameplay">x</a><a href="/jam/j1/results/communitys-voice?page=2">'
             '<a href="/jam/j1/results?page=3"><a href="/jam/j1/rate/5">a</a><a href="/jam/j1/rate/5">'
             '<a href="/jam/j1/rate/7">')
        self.assertEqual(jp.criteria_slugs(h, "j1"), ["best-gameplay", "communitys-voice"])
        self.assertEqual(jp.rate_ids(h, "j1"), ["5", "7"])
        self.assertEqual(jp.page_count(h, "/jam/j1/results"), 3)
        self.assertEqual(jp.page_count(h, "/jam/j1/results/communitys-voice"), 2)
        self.assertEqual(jp.page_count(h, "/jam/j1/results/best-gameplay"), 1)

    def test_relative_pager(self):
        self.assertEqual(jp.page_count(PAGER, "/jam/j1/results/communitys-voice"), 13)
        self.assertEqual(jp.page_count("<p>no pager</p>", "/jam/j1/results"), 1)


class StatsTests(unittest.TestCase):
    def test_fisher(self):
        g, l, t = jp.fisher(3, 1, 1, 3)
        self.assertAlmostEqual(g, 17 / 70)
        self.assertAlmostEqual(l, 69 / 70)
        self.assertAlmostEqual(t, 34 / 70)

    def test_holm(self):
        self.assertEqual(jp.holm({"a": 0.01, "b": 0.04, "c": 0.03}), {"a": 0.03, "c": 0.06, "b": 0.06})

    def test_perm(self):
        allv = [i / 100 for i in range(1, 101)]
        self.assertLess(jp.perm_better(allv[:5], allv, reps=2000), 0.01)
        self.assertGreater(jp.perm_better(allv[-5:], allv, reps=2000), 0.9)

    def test_spearman_and_median(self):
        self.assertAlmostEqual(jp.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertEqual(jp.median([3, 1, 2]), 2)
        self.assertEqual(jp.median([4, 1, 2, 3]), 2.5)

    def test_adjustment(self):
        rows = [row("a", {"C": {"rank": 1, "score": 4.0, "raw": 4.0}}, ratings=12),
                row("b", {"C": {"rank": 2, "score": round(4 * math.sqrt(5 / 10), 3), "raw": 4.0}}, ratings=5),
                row("c", {"C": {"rank": 3, "score": round(3 * math.sqrt(8 / 10), 3), "raw": 3.0}}, ratings=8)]
        a = jp.adjustment_check(rows, "C")
        self.assertEqual(a["penalized"], 2)
        self.assertAlmostEqual(a["implied_median"]["mean"], 10.0, places=1)
        self.assertEqual(a["min_ratings_unpenalized"], 12)
        self.assertEqual(a["max_ratings_penalized"], 8)


class SummaryTests(unittest.TestCase):
    def test_picks_vs_rest(self):
        rows = []
        for i in range(40):
            scores = {"Community": {"rank": i + 1, "score": 5 - i / 10, "raw": 5 - i / 10}}
            if i in (0, 1, 2):
                scores["Best Overall"] = {"rank": 1, "score": None, "raw": None}
            rows.append(row("g%d" % i, scores, team_size=2 if i < 6 else 1, content_ai="ai" if i >= 30 else "no-ai"))
        s = jp.summarize(rows)
        self.assertEqual(s["criteria"]["Best Overall"]["kind"], "hand-picked")
        self.assertEqual(s["criteria"]["Community"]["kind"], "rated")
        self.assertEqual(s["main_rated_criterion"], "Community")
        self.assertTrue(s["main_ranking_complete"])
        self.assertEqual(len(s["picks"]), 3)
        self.assertEqual(s["picks_in_main_ranking"]["in_top_10pct"], 3)
        self.assertLess(s["picks_in_main_ranking"]["perm_p_better_than_random"], 0.01)
        self.assertEqual(s["picks_vs_rest"]["team_2plus"]["picks"], "3/3")
        self.assertEqual(s["picks_vs_rest"]["team_2plus"]["rest"], "3/37")
        self.assertEqual(s["picks_vs_rest"]["ai_disclosed_itch"]["picks"], "0/3")
        self.assertEqual(set(s["preregistered"]["holm_p"]), set(jp.PREREGISTERED))
        self.assertAlmostEqual(s["criteria"]["Community"]["score_at_rank"]["30"], 2.1)

    def test_partial_read_is_flagged(self):
        # only the top 10 of a 200-entry ranking were read, plus one pick ranked #150 (what 0.1.0 did)
        rows = [row("g%d" % i, {"Community": {"rank": i + 1, "score": 5 - i / 100, "raw": 5 - i / 100}})
                for i in range(10)]
        rows.append(row("pick", {"Community": {"rank": 150, "score": 3.0, "raw": 3.0},
                                 "Best Overall": {"rank": 1, "score": None, "raw": None}}))
        s = jp.summarize(rows)
        self.assertFalse(s["main_ranking_complete"])
        self.assertLessEqual(s["picks_in_main_ranking"]["median_percentile"], 1.0)

    def test_all_rated_prefers_overall(self):
        rows = [row("g%d" % i, {"Fun": {"rank": i + 1, "score": 4 - i / 10, "raw": 4 - i / 10},
                                "Overall": {"rank": i + 1, "score": 3 - i / 10, "raw": 3 - i / 10}}) for i in range(5)]
        s = jp.summarize(rows)
        self.assertEqual(s["main_rated_criterion"], "Overall")
        self.assertEqual(s["picks"], [])
        self.assertNotIn("picks_vs_rest", s)
        self.assertAlmostEqual(s["rated_correlations_spearman"]["Fun ~ Overall"], 1.0)


if __name__ == "__main__":
    unittest.main()
