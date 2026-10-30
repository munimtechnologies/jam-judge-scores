"""Tests for grade_tgj02.py (Apache-2.0). By MV2 of Munim, Inc., made with AI agents (Anthropic Claude)."""
import csv
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade_tgj02 as g  # noqa: E402

CV = "Community's Voice"


def entry(i, n=100, ratings=None, browser=True, content_ai="no-ai", awards=(), med=14):
    """Entry ranked i+1 of n; scores fall with rank; below the jam's median ratings (med) itch scales the score."""
    ratings = ratings if ratings is not None else (20 if browser else 8)
    raw = round(4.8 - 3.0 * i / n, 3)
    score = raw if ratings >= med else round(raw * math.sqrt(ratings / med), 3)
    scores = {CV: {"rank": i + 1, "score": score, "raw": raw}}
    for a in awards:
        scores[a] = {"rank": 1, "score": None, "raw": None}
    return {"title": "Game %d" % i, "ratings": ratings, "scores": scores, "browser": browser, "content_ai": content_ai}


def jam(winners=(0, 3, 8), n=100):
    rows = [entry(i, n, browser=i % 2 == 0, content_ai="ai" if i % 3 == 0 else "no-ai") for i in range(n)]
    for a, w in zip(g.AWARDS, winners):
        rows[w]["scores"][a + (" Award" if a == "Best Visual Design" else "")] = {"rank": 1, "score": None, "raw": None}
    return rows


class GradeTests(unittest.TestCase):
    def test_thresholds_are_the_preregistered_ones(self):
        self.assertEqual((g.TOP_HALF, g.BEST_OVERALL_TOP, g.MEAN_PCT_MAX, g.ADJ_TOL, g.AI_SHARE_MIN,
                          g.BROWSER_RATIO_MIN, g.ALPHA), (0.5, 0.1, 0.3, 0.5, 0.29, 1.3, 0.05))
        self.assertEqual(g.CORE, ("P1", "P3", "P7"))
        self.assertEqual(g.AWARDS, ("Best Overall", "Best Gameplay", "Best Visual Design"))

    def test_good_case_all_hold(self):
        res = g.grade(jam())
        P = res["predictions"]
        self.assertEqual(res["community_criterion"], CV)
        self.assertTrue(P["P1"]["held"])
        self.assertTrue(P["P2"]["held"])           # Best Overall winner is #1 of 100
        self.assertAlmostEqual(P["P3"]["value"], (0.01 + 0.04 + 0.09) / 3, places=4)
        self.assertFalse(P["P4"]["held"])          # ...and that makes it the community's #1
        self.assertTrue(P["P5"]["held"])
        self.assertEqual(P["P5"]["value"]["ratings_median"], 14)  # half the entries have 20 ratings, half 8
        self.assertAlmostEqual(P["P5"]["value"]["implied_median"], 14, delta=0.2)
        self.assertTrue(P["P6"]["held"])           # 34 of 100 tick AI
        self.assertTrue(P["P7"]["held"])           # browser 20 ratings vs download 8
        self.assertTrue(P["P8"]["held"])           # AI tagging is unrelated to rank here
        self.assertEqual(res["core_held"], 3)

    def test_winner_outside_ranking_counts_against(self):
        rows = jam()
        rows.append({"title": "TapTap only", "ratings": None, "browser": None, "content_ai": "",
                     "scores": {"Best Gameplay": {"rank": 1, "score": None, "raw": None}}})
        for r in rows:
            r["scores"].pop("Best Gameplay", None) if r["title"] == "Game 3" else None
        res = g.grade(rows)
        self.assertIn(1.0, res["predictions"]["P1"]["value"])
        self.assertFalse(res["predictions"]["P1"]["held"])

    def test_missing_award_counts_against(self):
        rows = jam()
        for r in rows:
            r["scores"].pop("Best Overall", None)
        res = g.grade(rows)
        self.assertFalse(res["predictions"]["P1"]["held"])
        self.assertFalse(res["predictions"]["P2"]["held"])
        self.assertFalse(res["predictions"]["P4"]["held"])

    def test_low_winners_fail(self):
        res = g.grade(jam(winners=(60, 70, 80)))
        self.assertFalse(res["predictions"]["P1"]["held"])
        self.assertFalse(res["predictions"]["P3"]["held"])
        self.assertTrue(res["predictions"]["P4"]["held"])

    def test_ai_penalty_fails_p8(self):
        rows = [entry(i, 100, content_ai="ai" if i >= 50 else "no-ai") for i in range(100)]
        res = g.grade(rows)
        self.assertFalse(res["predictions"]["P8"]["held"])
        self.assertLess(res["predictions"]["P8"]["value"]["p_two_sided"], 0.001)

    def test_equal_ratings_fail_p7(self):
        rows = [entry(i, 60, ratings=15, browser=i % 2 == 0) for i in range(60)]
        self.assertFalse(g.grade(rows)["predictions"]["P7"]["held"])

    def test_mann_whitney(self):
        u, p_g, p_t = g.mann_whitney([4, 5, 6], [1, 2, 3])
        self.assertEqual(u, 9)
        self.assertLess(p_g, 0.05)
        self.assertGreater(g.mann_whitney([1, 2, 3], [4, 5, 6])[1], 0.95)
        self.assertEqual(g.mann_whitney([1, 1], [1, 1])[1:], (1.0, 1.0))

    def test_csv_round_trip_and_exclusion(self):
        rows = jam()
        d = tempfile.mkdtemp()
        p = os.path.join(d, "entries.csv")
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rate_id", "title", "ratings", "scores", "browser", "content_ai"])
            for i, r in enumerate(rows):
                w.writerow([i, r["title"], r["ratings"], json.dumps(r["scores"]), r["browser"], r["content_ai"]])
        back = g.load(p)
        self.assertEqual(len(back), 100)
        self.assertEqual(back[0]["browser"], True)
        self.assertEqual(back[1]["browser"], False)
        self.assertEqual(g.grade(back)["predictions"]["P3"]["value"], g.grade(rows)["predictions"]["P3"]["value"])
        self.assertEqual(len(g.load(p, ["game 0"])), 99)


if __name__ == "__main__":
    unittest.main()
