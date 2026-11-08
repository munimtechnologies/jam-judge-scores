# Apache-2.0. MV2, Munim, Inc. Made with AI agents (Anthropic Claude).
import unittest

import explore_h7 as e


class T(unittest.TestCase):
    def test_ranks_ties(self):
        self.assertEqual(e.ranks([3, 1, 3, 2]), [3.5, 1.0, 3.5, 2.0])

    def test_spearman_perfect(self):
        self.assertAlmostEqual(e.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(e.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)

    def test_analyse_counts_adjusted(self):
        rows = [{"ratings": k, "fun_score": f, "fun_raw": r, "visual_raw": r, "theme_raw": r}
                for k, f, r in [(3, 2.598, 3.0), (4, 3.0, 3.0), (4, 2.0, 2.0), (5, 4.0, 4.0)]]
        out = e.analyse(rows)
        self.assertEqual(out["entries_with_fun_adjusted"], 1)
        self.assertEqual(out["median_ratings"], 4.0)
        self.assertEqual(out["ratings_histogram"], {"3": 1, "4": 2, "5": 1})


if __name__ == "__main__":
    unittest.main()
