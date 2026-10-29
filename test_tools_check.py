# Tests for tools_check (offline). MV2 of Munim, Inc. Apache-2.0.
import os
import random
import unittest

import tools_check as tc

HERE = os.path.dirname(os.path.abspath(__file__))


class ToolsCheckTests(unittest.TestCase):
    def test_groups(self):
        self.assertEqual(tc.group([]), "no_answer")
        self.assertEqual(tc.group(["None of these"]), "none_only")
        self.assertEqual(tc.group(["Ziva"]), "tools_only")
        self.assertEqual(tc.group(["Convai", "Rosebud"]), "tools_only")
        self.assertEqual(tc.group(["Ziva", "None of these"]), "contradictory")

    def test_parts(self):
        self.assertEqual(tc.parts("Convai, Rosebud"), ["Convai", "Rosebud"])
        self.assertEqual(tc.parts(""), [])

    def test_holm(self):
        for got, want in zip(tc.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06]):
            self.assertAlmostEqual(got, want, places=12)
        self.assertEqual(tc.holm([0.5, 0.9]), [1.0, 1.0])

    def test_perm_test_same_and_apart(self):
        rng = random.Random(1)
        _, p_same = tc.perm_test([1.0, 2.0, 3.0] * 4, [1.0, 2.0, 3.0] * 4, 2000, rng)
        self.assertGreater(p_same, 0.9)
        diff, p_apart = tc.perm_test([4.0, 4.2, 4.1, 3.9] * 3, [2.0, 2.1, 1.9, 2.2] * 3, 2000, rng)
        self.assertAlmostEqual(diff, 2.0, places=6)
        self.assertLess(p_apart, 0.01)

    def test_real_census_counts(self):
        # data/slapjam-ai-1/entries.csv is the unmodified output of job slapjam1-census-v2 (2026-10-16 21:59Z)
        rows = tc.load(os.path.join(HERE, "data", "slapjam-ai-1", "entries.csv"))
        self.assertEqual(len(rows), 137)
        s = tc.analyse(rows, perms=200)
        g = s["groups"]
        self.assertEqual(g["none_only"]["entries"], 99)
        self.assertEqual(g["tools_only"]["entries"], 30)
        self.assertEqual(g["contradictory"]["entries"], 4)
        self.assertEqual(g["no_answer"]["entries"], 4)
        # hand sums from the CSV: tools-only Fun 76.238 / 30, contradictory 8.85 / 4, no answer 12.1 / 4
        self.assertAlmostEqual(g["tools_only"]["mean_fun_score"], 2.541, places=3)
        self.assertAlmostEqual(g["contradictory"]["mean_fun_score"], 2.212, delta=0.0011)
        self.assertAlmostEqual(g["no_answer"]["mean_fun_score"], 3.025, places=3)
        self.assertEqual(s["adjusted_titles"], ["Castle Mania"])
        self.assertIn("DREADFALL", s["contradictory_titles"])
        self.assertEqual(sum(s["top20_overall_by_group"].values()), 20)


if __name__ == "__main__":
    unittest.main()
