# Results: how far down the community ranking GDevelop's judges reach (BIG Game Jams #1-#9)

By MV2 of Munim, Inc. (mv2@munimtech.com). The study, code and this write-up were made with AI agents
(Anthropic Claude) working in his name. Text and data CC BY 4.0, code Apache-2.0.
Graded 2026-11-06 against [PREREGISTRATION-gdevelop-judges.md](PREREGISTRATION-gdevelop-judges.md),
which was committed before any results page was read.

## Bottom line

**4 of 6 predictions held. Core: P1 missed narrowly, P2 and P3 held. Secondary: P4 missed, P5 and P6 held.**

Across nine GDevelop jams, none of the 43 cash winners we could place had fewer ratings than its jam's
median, and the fewest any winner had was 9. The judges mostly picked from the top of the community
ranking (median winner rank 8), but not always: 7 of 43 winners ranked below 30th, and one ranked 86th of
370. In 7 of 9 jams, itch.io's few-ratings adjustment pushed at least one entry that would have been in
the raw top 10 out of the top 10.

For an entrant this means: being in the community top 10 is not required to win a judges' cash prize, but
in nine jams no entry has won one with fewer ratings than the jam's median.

## The run

- Data run `gdjudges-v4`: `judge_reach.py` 0.2.2, 2026-11-06. All nine jams were read (2,285 ranked
  entries on 119 results pages). For every jam: missing ranks 0, missing ratings 0, missing titles 0 and
  headline mismatches 0 (`data/gdevelop-judges/jams.csv`).
- 0.2.2 differed from the pre-registered 0.2 only in transport: it waits and retries when itch.io answers
  "429 Too Many Requests", and pauses longer between pages. Parsing, matching and counting are unchanged.
  The earlier run `gdjudges-v3` (0.2) read jams #1-#3 before it was rate-limited. We saw its partial output
  (for example jam #1: Hero Builder 1st with 94 ratings, //TO:DO 6th with 60, Northburg 7th with 55) before
  filing v4. The predictions were already public and were not changed.
- Ranks have gaps where entries were deleted after the jam; itch.io keeps the ranks it gave. Jam #1 lists
  225 rated entries but 190 are still on its results pages.

## Matching the 45 winners

The script matched 40 of 45 winners by exact title or a unique prefix, so the core predictions are
gradable (the bar was 40). The pre-registration allows manual fixes only by choosing a candidate the
script itself listed, with each fix disclosed. We made three (`data/gdevelop-judges/fixes.csv`):

| Jam | Winner (GDevelop's post) | Chosen itch.io entry | Rank | Ratings | Evidence |
|---|---|---|---|---|---|
| #3 | Sticky Keys (2nd) | Stickey Keys | 1 | 16 | one-letter spelling difference; first candidate |
| #4 | Carbon Ghost Decoder: 4D (2nd) | Carbon Ghost's Decoder: 4D | 49 | 21 | only the possessive differs; rank checked on its rate page |
| #5 | Unstable Dungeon (3rd) | Unstable Dungeon, rate/2732727 | 8 | 53 | two entries share the title; GDevelop's winners post credits this entry's team and also lists it 8th in the community vote; the other is by a different author and ranked 132nd |

Two winners could not be placed: "Ruined Ruins" (jam #1) and "Penguins Vs Ducks" (jam #7) are not on the
results pages, and no listed candidate is the same game. They were most likely deleted or retitled.

**The fixes are part of the pre-registered method, so the verdicts below use all 43 placed winners.**
The 40 automatic matches alone are reported too, because P1 depends on the choice.

## Grades

| | Prediction | 43 placed (graded) | 40 automatic only | Verdict |
|---|---|---|---|---|
| P1 (core) | at least 85% of winners rank in the top 30 | 36/43 = 83.7% | 34/40 = 85.0% | **missed** |
| P2 (core) | under 20% of winners have fewer ratings than the jam median | 0/43 = 0% | 0/40 | **held** |
| P3 (core) | in at least 6 of 9 jams a raw top-10 entry is pushed out of the top 10 | 7 of 9 | 7 of 9 | **held** |
| P4 | no winner ranks worse than 60th | worst 86th | worst 86th | **missed** |
| P5 | median winner rank 10 or better | 8 | 7.5 | **held** |
| P6 | every winner has at least 5 ratings | fewest 9 | fewest 9 | **held** |

P1 sits right on its threshold: it holds at exactly 85.0% on the automatic matches and misses at 83.7%
once the three disclosed fixes are added (Carbon Ghost's Decoder ranked 49th). We grade it as missed. The
seven winners below 30th ranked 31, 42, 48, 49, 51, 54 and 86. P4 misses because of SURVIVE 999, the
judges' 3rd place in jam #7, ranked 86th of 370 with 39 ratings. That is above the jam's median of 20
ratings: the judges went far down for it, but it was not a low-rating entry.

## Reproduction check (2026-11-07)

The published `grade.py` and its tests were run again on the published data files alone, in a fresh sandbox
with no network (job `gdjudges-grade-v1`, 2026-11-07 00:00 UTC). The tests passed, and every number above came
out the same: automatic matches 40, in the top 30 34 (85.0%), P1 held; with the three fixes 43 matched, 24 in
the top 10, 36 in the top 30 (83.72%), 0 below the median, 7 of 9 jams with a pushed-out entry, worst rank 86,
median rank 8, fewest ratings 9, ranks below 30th 31, 42, 48, 49, 51, 54 and 86; P1 missed, P2 and P3 held, P4
missed, P5 and P6 held.

## More counts

- 24 of 43 winners were in the community top 10, 30 of 40 (automatic) in the top 20. The pre-registration
  noted, from GDevelop's posts, 25 of 45 winners in the top 10; with two winners unplaced, 24 of 43 fits.
- Winners per jam ranked below 30th: #1 1, #2 1, #3 0, #4 1, #5 1, #6 0, #7 1, #8 2, #9 0. In only 3 jams
  (#3, #6, #9) were all placed winners in the top 30.
- The most-rated entry pushed out of a raw top 10 had 38 ratings (jam #1, median 22); in jam #6 the one
  pushed out had at most 4. In jam #3 three were pushed out, for example one with the third-best raw score
  (4.033) and 12 ratings (median 16) that finished 45th.
- The community's #1 entry won a judges' cash prize in 6 of 9 jams (#1, #3, #4, #7, #8, #9).

## Limits

- Rating counts and ranks are as they stand today, not what the judges saw. Deleted entries are gone,
  which also shifts each jam's median a little; we use the median over entries still on the results pages.
- One organiser, nine jams, five cash winners each. "No winner below the median" is 0 of 43: a strong
  pattern, not a rule, and judges may have skipped low-rating entries for other reasons (for example
  because those entries were weaker).
- Winner titles were copied by hand from GDevelop's posts; two of 45 could not be placed.

## Reproduce

`gdevelop-judges/judge_reach.py` (0.2.2) reads the results pages; `gdevelop-judges/grade.py` grades
`data/gdevelop-judges/picks.csv` and `jams.csv`, with and without `fixes.csv`. Raw HTML and the full
per-entry lists are not published here; the script re-reads them from itch.io.

## Prior art

Searches on 2026-11-06 found itch.io's adjustment formula, organisers' complaints about it (for example
Ebitengine Game Jam 2023) and MV2's own earlier jam studies, but no count that places a jam series'
judged cash winners in the community ranking.
