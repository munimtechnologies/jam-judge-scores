# Results: do the Slapjam #1 judge-score patterns hold in Slapjam #2?

Graded 2026-11-08 from data read on 2026-11-07/08 (23:45-00:23 UTC), after Slapjam #2 judging closed
(2026-11-07 15:00 UTC). Predictions: `PREREGISTRATION-slapjam2.md` (committed before the jam opened on
2026-10-29) and `PREREGISTRATION-slapjam2-ADDENDUM.md` (2026-10-30, before submissions closed). Graded exactly
as written. MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents (Anthropic Claude). Text CC BY 4.0,
code Apache-2.0.

## Verdict

**5 of 9 predictions held. The core claim (H1, H2, H4 and H5 together) did not replicate**: H4 and H5 failed.
The sensitivity run without MV2's two entries gives the same verdict for every prediction.

Two of Slapjam #1's patterns carried over: the three criteria still move together, and Theme Following is
still scored most generously. The third did not: in Slapjam #1 the most fun game lost the top spot to a more
balanced, on-theme game. In Slapjam #2 the most fun game won outright, and four of the five top games had at
least one criterion below the pre-registered floor.

## Each prediction (primary run: all 209 scored entries)

| ID | Prediction (Slapjam #1 value) | Slapjam #2 | Held? |
|---|---|---|---|
| H0 | 50-145 scored entries; context only (137) | **209** | no |
| H1 | every pairwise Pearson r of the criteria >= 0.50 (0.64-0.72) | Fun~Visual 0.735, Fun~Theme 0.725, Visual~Theme 0.584 | **yes** |
| H2 | Theme Following has the highest mean (3.12 vs 2.82 / 2.67) | Theme 2.774, Visual 2.288, Fun 2.256 | **yes** |
| H3 | Fun mean below Visual Appeal mean (2.67 vs 2.82) | 2.256 vs 2.288 (gap 0.032) | yes |
| H4 | Overall #1 is not the top-Fun entry (4.0 vs 4.4) | Speed Slash is Overall #1 **and** top Fun (4.5) | **no** |
| H5 | every top-5 entry has Theme >= 3.8 and no criterion under 3.5 | 4 of 5 break it (see below) | **no** |
| H6 | rank-5 Overall between 3.60 and 4.30 (3.95) | 3.667 | yes |
| H7 | \|Spearman(ratings count, Fun)\| < 0.20 (-0.002) | **0.451** | no |
| H8 | sponsor-tools-only vs "None of these" only: no difference at Holm p < 0.05 | 16 vs 156 entries; smallest raw p 0.329, all Holm p 1.0 | yes |

Bold "yes"/"no" marks the core predictions (and H0, which is context).

H5 in detail (Fun / Visual Appeal / Theme Following):

| Overall rank | Entry | Fun | Visual | Theme | Breaks H5 because |
|---|---|---|---|---|---|
| 1 | Speed Slash | 4.50 | 3.25 | 4.25 | Visual under 3.5 |
| 2 | Escape Velocity | 3.75 | 4.50 | 3.50 | Theme under 3.8 |
| 3 | Shrinestone | 3.75 | 3.50 | 4.00 | (meets it) |
| 4 | Snailracer: Fast as Shell | 3.50 | 3.75 | 3.75 | Theme under 3.8 |
| 5 | DragonRacers | 3.40 | 3.80 | 3.80 | Fun under 3.5 |

H8 groups by the jam's question "Which of these did your game use?": 156 answered only "None of these", 16
named only sponsor tools (Rosebud, Ziva, PixelLab, Jamboree), 37 gave no answer. Tools-minus-none differences:
Fun +0.091, Visual +0.174, Theme +0.088, Overall +0.118 (20,000 permutations, seed 1). As the
pre-registration says, with 16 entries in one group a "held" here does not show the tools make no difference.

## Sensitivity run (addendum): without Rush Order and Nova Slingshot

207 entries. Every prediction has the same outcome. The largest changes: Fun~Visual r 0.737 (was 0.735),
Fun mean 2.252 (was 2.256), Theme mean 2.772 (was 2.774), H7 Spearman 0.457 (was 0.451). Neither of MV2's
entries is in the top 5, so H4-H6 are unchanged. Both of his entries were scored (Rush Order 4 ratings,
Nova Slingshot 3), so the addendum's "excludes nothing" case did not arise.

## What changed from the pre-registered method (transport only)

- The census read itch.io through `run_census.py`, which imports the frozen `jam_census.py` unchanged from
  this repository and swaps only its download function for one that waits and retries on HTTP 429
  (honouring Retry-After). The page delay was 5 s instead of the pre-registered 1.5 s, which is slower and
  politer. Parsing, the sample, the statistics and every threshold are the frozen code.
- The grading job downloaded `jam_census.py`, `grade_prereg.py`, `tools_check.py`, their tests and both
  pre-registration files from this repository's public `main` branch, and ran the tests first (all passed).
- No parser fix was needed.

## Hand check

Three rows of `data/slapjam-ai-2/entries.csv` were compared with their itch.io rate pages on 2026-11-08:
Speed Slash (rate/5271610), Umbrella (rate/5265836) and DragonRacers (rate/5258581). All three match on
every criterion's rank, adjusted score, raw score and ratings count. The equal-weight Overall the grader
computes also equals itch.io's own Overall for both entries checked (Speed Slash 4.000, #1; DragonRacers
3.667, #5).

## Limits, and one caution about H7

- **H7 is partly mechanical.** The grader uses itch.io's adjusted scores, the same as for Slapjam #1. itch.io
  scales an entry's score by sqrt(n / median) when it has fewer ratings (n) than the jam's median. In
  Slapjam #2 the median was 4 ratings and 77 of 209 entries had only 3, so their scores were multiplied by
  0.866. That alone ties ratings count to Fun. Slapjam #1 (H7 = -0.002) did not have this many short panels.
  The pre-registered result stands as graded (H7 failed). The exploratory re-check on raw scores is below.
- Panels are small (3-6 ratings per entry), so one judge can move a score by up to about 0.8.
- These are patterns in one jam's scores, not causes. The jam grew from 137 to 209 scored entries, which
  may change who judges and how.
- Scores are as itch.io showed them on 2026-11-07/08. Deleted entries are missing.

## Exploratory re-check of H7 on raw scores (not pre-registered)

This section was added after grading. It was **not** pre-registered and does not change any verdict above:
H7 stays failed. It asks how much of H7's 0.451 comes from itch.io's below-median scaling. Run on
2026-11-08 by `slapjam2-explore/explore_h7.py` (its 3 unit tests passed first) on the published
`data/slapjam-ai-2/entries.csv`. Output: `results/slapjam2/explore-h7-primary.json` and
`results/slapjam2/explore-h7-sens.json`.

Ratings per entry: 3 ratings: 77 entries, 4: 107, 5: 24, 6: 1 (median 4). Exactly the 77 entries with 3
ratings had their Fun score scaled.

| Spearman with ratings count | All 209 | Without MV2's 2 entries (207) |
|---|---|---|
| Fun, adjusted (what H7 graded) | 0.451 | 0.457 |
| Fun, raw | 0.262 | 0.271 |
| Visual Appeal, raw | 0.245 | 0.250 |
| Theme Following, raw | 0.185 | 0.191 |
| Fun, raw, only entries with >= 4 ratings (132 / 131) | 0.252 | 0.254 |

What this says, read plainly:

- The scaling explains a bit under half of H7's number (0.451 to 0.262 on raw Fun), but not all of it.
- On raw scores the link is still above H7's 0.20 bound for Fun and Visual Appeal, and it stays at 0.25
  among entries that were never scaled. So in Slapjam #2, entries that got more ratings really were rated as
  more fun, unlike Slapjam #1 (-0.002).
- This data cannot say why. Two candidates: better games may draw extra raters, or the jam's judging may
  have handed out panels unevenly. Neither was tested.
- Lesson for later pre-registrations in this repository: say whether a test uses adjusted or raw scores, and
  predict both.

## Files

- `data/slapjam-ai-2/entries.csv`: the census (rate id, title, ratings count, rank / adjusted score / raw
  score per criterion, tools answer). No author names or handles.
- `results/slapjam2/primary-grade.json`, `results/slapjam2/sens-grade.json`: the grader's output.
- `results/slapjam2/explore-h7-primary.json`, `results/slapjam2/explore-h7-sens.json`: the exploratory
  raw-score re-check above.
- `run_census.py`, `test_run_census.py`: the transport wrapper described above.
- `slapjam2-explore/explore_h7.py`, `slapjam2-explore/test_explore_h7.py`: the exploratory raw-score re-check
  (not part of the grading).

Reproduce:

```sh
python run_census.py --jam slapjam-ai-2 --out out --delay 5
python grade_prereg.py --csv out/entries.csv --out out/primary
python grade_prereg.py --csv out/entries.csv --out out/sens --exclude-title "Rush Order" --exclude-title "Nova Slingshot"
python slapjam2-explore/explore_h7.py --csv data/slapjam-ai-2/entries.csv --out out/explore-primary
python slapjam2-explore/explore_h7.py --csv data/slapjam-ai-2/entries.csv --out out/explore-sens --exclude-title "Rush Order" --exclude-title "Nova Slingshot"
```

Scores on itch.io can change if entries are deleted, so a re-read may differ slightly from this census.
