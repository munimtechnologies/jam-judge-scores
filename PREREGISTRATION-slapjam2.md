# Pre-registration: do the Slapjam #1 judge-score patterns hold in Slapjam #2?

MV2 of Munim, Inc. (made with AI agents, Anthropic Claude). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-29 at about 02:45 UTC, about 12 hours BEFORE Slapjam #2 opens (2026-10-29 15:00 UTC) and
before any entry exists. The git commit that adds this file is its public timestamp. The thresholds below and
in `grade_prereg.py` are fixed from that commit on; any later change would be a new, separately dated file.

## Why
[FINDINGS-slapjam1.md](FINDINGS-slapjam1.md) found patterns in the 137 judge-scored entries of Slapjam #1,
a game jam where AI use is required and only hosts and approved judges rate. One jam is one sample. Slapjam #2
uses the same three criteria (Fun, Visual Appeal, Theme Following), the same judges-only rating and the same
equal-weight Overall, so it is a fair test of whether those patterns are general or were luck. Apart from MV2's own Slapjam #1
write-up we found no analysis of Slapjam judge scores, and no pre-registered replication of judge-score
patterns in any game jam (web searches 2026-10-16 and 2026-10-29). The nearest academic work, "An Empirical
Study of the Characteristics of Popular Game Jams and Their High-ranking Submissions on itch.io" (FDG '20,
doi 10.1145/3402942.3402981), studies jam and entry features, not judge criteria, and was not pre-registered.
A failed prediction will be reported as plainly as a held one.

## Data and method (fixed now)
- After judging ends (2026-11-07 15:00 UTC) and the results page is public, run
  `python jam_census.py --jam slapjam-ai-2 --out out/` (public results and rate pages only, which itch.io's
  robots.txt allows; one request every 1.5 s; no author handles stored), then
  `python grade_prereg.py --csv out/entries.csv --out out/` (20,000 permutations, seed 1).
- Sample: every entry with all three criteria scores. Overall = equal-weight mean of the three, as the
  Slapjam #2 page says. Ties at 5th place are all counted as top 5.
- MV2 enters Slapjam #2 himself. The primary analysis includes every entry. A sensitivity run with
  `--exclude-title "<his entry's title>"` is reported next to it; if the two disagree on any prediction,
  both are shown and the primary result stands.
- If the census cannot read the scores (itch.io layout change), the parser may be fixed, but no threshold.

## Predictions (Slapjam #1 value in brackets)
| Id | Prediction | #1 |
|---|---|---|
| H0 | Between 50 and 145 scored entries (context, not a finding) | 137 |
| H1 | Every pairwise Pearson correlation among Fun, Visual Appeal and Theme Following is at least 0.50 | 0.64-0.72 |
| H2 | Theme Following has the highest mean of the three criteria | 3.12 vs 2.82 / 2.67 |
| H3 | Fun has a lower mean than Visual Appeal | 2.67 vs 2.82 |
| H4 | The Overall #1 entry is not the top-Fun entry (no entry tied for Overall #1 has the top Fun score) | 4.0 vs 4.4 |
| H5 | Every top-5 Overall entry has Theme Following at least 3.8 and no criterion under 3.5 | Theme >= 4.0, min 3.7 |
| H6 | The rank-5 Overall score is between 3.60 and 4.30 | 3.95 |
| H7 | The number of ratings an entry got and its Fun score are unrelated: abs(Spearman) under 0.20 | -0.002 |
| H8 | Entries that ticked only sponsor tools vs only "None of these" on the tools checklist: no criterion and no Overall difference at Holm-adjusted p < 0.05 (two-sided permutation test). Not testable, and reported as such, if either group has fewer than 10 entries | smallest p 0.17 |

The core claim of the Slapjam #1 write-up is H1, H2, H4 and H5 together ("the criteria move together, Theme
is scored most generously, and a balanced game beats a fun but off-theme one"). It counts as replicated only
if all four hold. H3 (a 0.15 gap in #1) and H4 (one data point in #1) are the riskiest.

## Limits, stated in advance
- Judge panels are small (3-7 ratings per entry in #1), so single judges move scores by up to 0.8.
- These are patterns, not causes; a held prediction does not show why judges score this way.
- H8 is a test of "no detectable difference" with low power; holding it does not show the tools have no effect.
- The tools checklist wording may change; the grader takes the question whose answers include
  "None of these" most often.

## Self-check
`test_grade_prereg.py` confirms that Slapjam #1's own data meet every prediction (they were set from it,
loosened for judge noise), so a failure in Slapjam #2 means #2 differs, not that the grader is broken.
