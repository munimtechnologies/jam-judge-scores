# Tests for jam_census (offline; fixtures shaped like itch.io jam pages). MV2 of Munim, Inc. Apache-2.0.
import unittest

import jam_census as jc

RESULTS = """<html><body>
<div class="game_rank"><h2><a href="https://a.itch.io/one">One</a></h2>
<a href="/jam/test-jam/rate/111">View submission</a><a href="/jam/test-jam/rate/111">again</a></div>
<div class="game_rank"><h2><a href="https://b.itch.io/two">Two</a></h2><a href="/jam/test-jam/rate/222">x</a></div>
<a href="/jam/other-jam/rate/999">other jam</a>
<div class="pager"><a href="?page=2">2</a><a href="?page=7">7</a></div>
</body></html>"""

# the field_responses markup is copied from a real Slapjam #1 rate page (2026-10-16); the comment is made up
RATE = """<html><head><title>King&#039;s Last Stand by SomeAuthor for Slapjam AI - itch.io</title>
<script>var x = "Fun #9 1.0 1.0";</script></head><body><section>
<div class="field_responses"><p><strong>Which of these did your game use?</strong><br/><div class="badges"><div class="badge"><div class="badge_summary"><strong>Tool A</strong></div></div><div class="badge"><div class="badge_summary"><strong>Tool B</strong></div></div></div></p></section>
<section class="jam_comment_form"><h2>Leave a comment</h2></section>
<div class="comment"><p>Is this the actual game from the ad?</p><p>Submitted by someauthor &mdash; 9 hours before the deadline</p></div>
<h2>Results</h2>
<table><tr><th>Criteria</th><th>Rank</th><th>Score*</th><th>Raw Score</th></tr>
<tr><td><a href="/jam/x/results/fun">Fun</a></td><td>#1</td><td><strong>4.400</strong></td><td>4.400</td></tr>
<tr><td>
  Visual Appeal
</td><td>#8</td><td>3.800</td><td>3.800</td></tr>
<tr><td>Theme Following</td><td>#41</td><td>3.400</td><td>3.400</td></tr></table>
<p>Ranked from 5 ratings. Score is adjusted from raw score by the median number of ratings per game in the jam.</p>
</body></html>"""


class CensusTests(unittest.TestCase):
    def test_rate_ids_in_order_without_repeats_or_other_jams(self):
        self.assertEqual(jc.rate_ids(RESULTS, "test-jam"), ["111", "222"])

    def test_page_count(self):
        self.assertEqual(jc.page_count(RESULTS), 7)
        self.assertEqual(jc.page_count("<p>no pager</p>"), 1)

    def test_parse_rate_page(self):
        r = jc.parse_rate_page(RATE)
        self.assertEqual(r["title"], "King's Last Stand")
        self.assertEqual((r["fun_rank"], r["fun_score"], r["fun_raw"]), (1, 4.4, 4.4))
        self.assertEqual((r["visual_appeal_rank"], r["visual_appeal_score"]), (8, 3.8))
        self.assertEqual((r["theme_following_rank"], r["theme_following_score"]), (41, 3.4))
        self.assertEqual(r["ratings"], 5)

    def test_answers_keep_every_ticked_box_and_skip_comments(self):
        r = jc.parse_rate_page(RATE)
        self.assertEqual(r["answers"], {"Which of these did your game use?": "Tool A, Tool B"})
        self.assertNotIn("someauthor", repr(r))

    def test_text_answer(self):
        h = '<div class="field_responses"><p><strong>Team size?</strong><br/>Two people</p></div>'
        self.assertEqual(jc.form_answers(h), {"Team size?": "Two people"})
        self.assertEqual(jc.form_answers("<p><strong>Q?</strong><br/>A</p>"), {})

    def test_scripts_are_ignored(self):
        r = jc.parse_rate_page("<script>Fun #9 1.0 1.0</script>")
        self.assertNotIn("fun_rank", r)

    def test_title_keeps_no_author(self):
        self.assertEqual(jc.game_title("A by B for C - itch.io"), "A")
        self.assertEqual(jc.game_title("Stand by Me by Someone for Jam - itch.io"), "Stand by Me")
        self.assertEqual(jc.game_title("Plain - itch.io"), "Plain")

    def test_split_answer(self):
        self.assertEqual(jc.split_answer("Tool A, Tool B"), ["Tool A", "Tool B"])
        self.assertEqual(jc.split_answer("None of these"), ["None of these"])

    def test_rank_correlations(self):
        self.assertEqual(jc.ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])
        self.assertAlmostEqual(jc.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertAlmostEqual(jc.spearman([1, 2, 3, 4], [1, 4, 9, 16]), 1.0)
        self.assertAlmostEqual(jc.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(jc.pearson([1, 1, 1], [1, 2, 3]))

    def test_spread(self):
        s = jc.spread([1.0, 2.0, 3.0, 4.0])
        self.assertEqual((s["mean"], s["median"], s["min"], s["max"]), (2.5, 2.5, 1.0, 4.0))
        self.assertAlmostEqual(s["sd"], 1.291, places=3)

    def test_summary_groups_answers(self):
        rows = []
        for i in range(8):
            r = jc.parse_rate_page(RATE)
            r["fun_score"] = 3.0 + i * 0.1
            r["answers"] = {"Which of these did your game use?": "Tool A" if i < 4 else "None of these",
                            "Have an account?": "Log in"}
            rows.append(r)
        rows[0]["answers"]["Which of these did your game use?"] = "Tool A, None of these"
        rows.append({"title": "The jam page", "ratings": None, "answers": {}})
        s = jc.summarize(rows)
        self.assertEqual(s["entries"], 8)
        self.assertEqual(s["pages_without_scores"], ["The jam page"])
        q = s["answers"]["Which of these did your game use?"]
        self.assertEqual(q["parts"]["Tool A"]["entries"], 4)
        self.assertAlmostEqual(q["parts"]["Tool A"]["mean_with"]["fun_score"], 3.15)
        self.assertEqual(q["parts"]["None of these"]["entries"], 5)
        self.assertEqual((q["entries_ticking_several"], q["entries_ticking_none_and_a_tool"]), (1, 1))
        self.assertEqual(len(s["top10_by_fun"]), 8)
        # overall = equal-weight mean of the three criteria; the best here is fun 3.7 with 3.8 and 3.4
        self.assertAlmostEqual(s["overall_needed"]["rank_1"], round((3.7 + 3.8 + 3.4) / 3, 3))


if __name__ == "__main__":
    unittest.main()
