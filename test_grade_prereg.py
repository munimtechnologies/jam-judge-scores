# Tests for grade_prereg (offline). MV2 of Munim, Inc. Apache-2.0.
import csv
import json
import os
import tempfile
import unittest

import grade_prereg as gp

HERE = os.path.dirname(os.path.abspath(__file__))
SLAPJAM1 = os.path.join(HERE, "data", "slapjam-ai-1", "entries.csv")
Q = "Which of these did your game use?"


def mk(title, fun, vis, theme, ratings=5, answer=None):
    r = {"title": title, "ratings": ratings, "fun_score": fun, "visual_appeal_score": vis,
         "theme_following_score": theme, "answers": {Q: answer} if answer else {}}
    r["overall"] = (fun + vis + theme) / 3
    return r


def by_id(results):
    return {r["id"]: r for r in results}


class Slapjam1Tests(unittest.TestCase):
    """The predictions were loosened from Slapjam #1, so #1's own data must meet every one of them."""

    @classmethod
    def setUpClass(cls):
        cls.rows = gp.load(SLAPJAM1)
        cls.results = by_id(gp.grade(cls.rows, perms=2000, seed=1))

    def test_entry_count(self):
        self.assertEqual(len(self.rows), 137)

    def test_every_prediction_holds_on_slapjam1(self):
        for pid, r in self.results.items():
            self.assertIs(r["held"], True, pid)
        v = gp.verdict(list(self.results.values()))
        self.assertEqual((v["held"], v["graded"], v["core_replicated"]), (9, 9, True))

    def test_values_match_the_published_findings(self):
        c = self.results["H1"]["value"]
        self.assertAlmostEqual(c["fun_score~visual_appeal_score"], 0.72, delta=0.006)
        self.assertAlmostEqual(c["fun_score~theme_following_score"], 0.67, delta=0.006)
        self.assertAlmostEqual(c["visual_appeal_score~theme_following_score"], 0.64, delta=0.006)
        m = self.results["H2"]["value"]
        self.assertAlmostEqual(m["fun_score"], 2.67, delta=0.006)
        self.assertAlmostEqual(m["visual_appeal_score"], 2.82, delta=0.006)
        self.assertAlmostEqual(m["theme_following_score"], 3.12, delta=0.006)
        self.assertEqual(self.results["H4"]["value"]["overall_1"], ["Keep It Crispy"])
        self.assertEqual(self.results["H4"]["value"]["top_fun"], 4.4)
        self.assertEqual(len(self.results["H5"]["value"]), 5)
        self.assertAlmostEqual(self.results["H6"]["value"], 3.952, places=3)
        self.assertLess(abs(self.results["H7"]["value"]), 0.01)
        h8 = self.results["H8"]["value"]
        self.assertEqual(h8["question"], Q)
        self.assertEqual((h8["groups"]["tools_only"], h8["groups"]["none_only"]), (30, 99))
        self.assertGreater(min(t["p_holm"] for t in h8["tests"]), 0.1)


class SyntheticTests(unittest.TestCase):
    def rows(self):
        return [mk("A", 4.0, 4.2, 4.6), mk("B", 3.8, 4.5, 4.2), mk("C", 4.4, 3.8, 3.4), mk("D", 3.0, 3.1, 3.5),
                mk("E", 2.5, 2.9, 3.2), mk("F", 2.0, 2.4, 2.8), mk("G", 1.5, 2.0, 2.6)]

    def test_top_fun_winning_overall_breaks_H4(self):
        rows = self.rows()
        rows.append(mk("Z", 4.8, 4.8, 4.8))
        self.assertIs(by_id(gp.grade(rows, perms=50))["H4"]["held"], False)
        self.assertIs(by_id(gp.grade(self.rows(), perms=50))["H4"]["held"], True)

    def test_weak_theme_in_top5_breaks_H5(self):
        r = by_id(gp.grade(self.rows(), perms=50))["H5"]
        self.assertIn("C", [e["title"] for e in r["value"]])  # Theme 3.4 < 3.8
        self.assertIs(r["held"], False)

    def test_ties_at_fifth_are_all_kept(self):
        rows = self.rows() + [mk("E2", 2.5, 2.9, 3.2)]
        self.assertEqual(len(by_id(gp.grade(rows, perms=50))["H5"]["value"]), 6)

    def test_small_tools_group_is_not_testable(self):
        rows = self.rows()
        rows[0]["answers"] = {Q: "Ziva"}
        for r in rows[1:]:
            r["answers"] = {Q: "None of these"}
        results = gp.grade(rows, perms=50)
        self.assertIsNone(by_id(results)["H8"]["held"])
        self.assertIn("H8", gp.verdict(results)["not_testable"])

    def test_tools_question_found_under_new_wording(self):
        rows = self.rows()
        for i, r in enumerate(rows):
            r["answers"] = {"Team size?": "Solo", "Tick every listed tool you used": "Ziva" if i % 2 else "None of these"}
        self.assertEqual(gp.tools_question(rows), "Tick every listed tool you used")
        self.assertIsNone(gp.tools_question(self.rows()))

    def test_tools_difference_is_detected(self):
        rows = [mk("t%d" % i, 4.0 + i % 3 * 0.1, 4.1, 4.2, answer="Ziva") for i in range(12)]
        rows += [mk("n%d" % i, 2.0 + i % 3 * 0.1, 2.1, 2.2, answer="None of these") for i in range(12)]
        self.assertIs(by_id(gp.grade(rows, perms=500))["H8"]["held"], False)

    def test_load_skips_unscored_and_excluded_rows(self):
        cols = ["rate_id", "title", "ratings", "fun_score", "visual_appeal_score", "theme_following_score", "answers"]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "entries.csv")
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerow(["1", "Jam page", "", "", "", "", ""])
                w.writerow(["2", "Mine", "4", "3.0", "3.0", "3.0", json.dumps({Q: "None of these"})])
                w.writerow(["3", "Other", "5", "2.0", "3.0", "4.0", ""])
            self.assertEqual([r["title"] for r in gp.load(p)], ["Mine", "Other"])
            rows = gp.load(p, exclude=["Mine"])
            self.assertEqual([r["title"] for r in rows], ["Other"])
            self.assertAlmostEqual(rows[0]["overall"], 3.0)
            self.assertEqual(rows[0]["answers"], {})


if __name__ == "__main__":
    unittest.main()
