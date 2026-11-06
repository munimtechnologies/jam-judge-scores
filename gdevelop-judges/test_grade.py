# Tests for grade.py. MV2 of Munim, Inc.; made with AI agents. Apache-2.0.
import csv
import os
import tempfile
import unittest

import grade

PICK_KEYS = ["jam", "place", "title", "matched_title", "match", "rank", "ratings", "score", "raw",
             "ranked_in_jam", "rank_pct", "median_ratings_ranked", "raw_rank", "candidates"]


def pick(jam, place, rank, ratings, median=10):
    return {"jam": str(jam), "place": str(place), "title": "T%d%d" % (jam, place), "matched_title": "",
            "match": "exact" if rank != "" else "none", "rank": str(rank), "ratings": str(ratings),
            "score": "", "raw": "", "ranked_in_jam": "100", "rank_pct": "", "median_ratings_ranked": str(median),
            "raw_rank": "", "candidates": ""}


def jams(displaced):
    return [{"jam": str(i + 1), "slug": "jam-%d" % (i + 1), "raw_top_displaced": str(d)} for i, d in enumerate(displaced)]


class GradeTest(unittest.TestCase):
    def test_thresholds_exact(self):
        # 40 matched, 34 in top 30 = exactly 85% -> P1 holds; 8 below median = 20% -> P2 fails (needs < 20%).
        ps = [pick(1, i, 5, 20) for i in range(34)] + [pick(1, 100 + i, 40, 20) for i in range(6)]
        for p in ps[:8]:
            p["ratings"] = "3"
        r = grade.grade(ps, jams([1, 1, 1, 1, 1, 1, 0, 0, 0]))
        self.assertEqual(r["matched"], 40)
        self.assertTrue(r["core_gradable"])
        self.assertTrue(r["P1"])
        self.assertFalse(r["P2"])
        self.assertTrue(r["P3"])
        self.assertTrue(r["P4"])
        self.assertTrue(r["P5"])
        self.assertFalse(r["P6"])

    def test_not_gradable_below_40(self):
        ps = [pick(1, i, 1, 20) for i in range(39)] + [pick(1, 99, "", "")]
        r = grade.grade(ps, jams([0] * 9))
        self.assertEqual(r["matched"], 39)
        self.assertIsNone(r["P1"])
        self.assertIsNone(r["P2"])
        self.assertIsNone(r["P3"])
        self.assertFalse(r["P3"] is True)

    def test_equal_to_median_is_not_below(self):
        ps = [pick(1, i, 1, 10, median=10) for i in range(40)]
        self.assertEqual(grade.grade(ps, jams([0] * 9))["below_median"], 0)

    def test_fix_reads_entry_by_rate_id(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "jam-1.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "title", "ratings", "score", "raw", "criterion", "rate_id"])
            w.writerow([8, "Same", 53, 3.6, 3.6, "Overall", "111"])
            w.writerow([132, "Same", 31, 2.6, 2.6, "Overall", "222"])
        ps = [pick(1, 1, "", "")]
        fixed = grade.apply_fixes(ps, [{"jam": "1", "place": "1", "chosen_title": "Same", "chosen_rate_id": "111"}],
                                  jams([0]), d)
        self.assertEqual(fixed[0]["rank"], "8")
        self.assertEqual(fixed[0]["ratings"], "53")
        self.assertEqual(ps[0]["rank"], "")  # input untouched
        with self.assertRaises(ValueError):
            grade.apply_fixes(ps, [{"jam": "1", "place": "1", "chosen_title": "Other", "chosen_rate_id": "222"}],
                              jams([0]), d)


if __name__ == "__main__":
    unittest.main()
