# Pre-registration: GDevelop BIG Game Jam #10 judges' winners

By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents (Anthropic Claude) working in his name.
Text CC BY 4.0, code Apache-2.0. Committed on 2026-11-06, the jam's opening day (submissions Nov 6 19:00 -
Nov 15 20:00, then a week of community rating), before any entry was rated and before any result exists.
MV2 is himself entering this jam; see M1 below.

## Why

`RESULTS-gdevelop-judges.md` placed 43 of the 45 cash winners of GDevelop's BIG Game Jams #1-#9 in their
jams' community rankings: none had fewer ratings than the jam's median, the median winner ranked 8th, and
7 ranked below 30th. This file tests, on a jam that has not happened yet, whether those patterns carry over.

## Method (fixed now)

1. When GDevelop posts the #10 winners, copy the five Judges' Award titles by hand into a picks file in the
   same format as `gdevelop-judges/judge_picks.csv` (jam 10, slug `gdevelop-big-game-jam-10`).
2. Run `gdevelop-judges/judge_reach.py` 0.2.2, unchanged, on that file within 14 days of the winners post.
3. Matching and fixes follow the #1-#9 rules: exact title or unique prefix; a manual fix only by choosing a
   candidate the script listed, with each fix and its evidence published.
4. "Median" is the median ratings count over the ranked entries on the results pages, as in #1-#9.
5. If fewer than 4 of the 5 winners can be placed, Q1 and Q2 are reported as not gradable.
6. Every prediction is reported, held or not.

## Predictions

Base rates are from jams #1-#9 (43 placed winners).

Core
- **Q1.** None of the placed #10 winners has fewer ratings than the jam's median. (#1-#9: 0 of 43.)
- **Q2.** At least 3 of the 5 winners rank in the community top 30. (#1-#9: true in all 9 jams.)

Secondary
- **Q3.** The community's #1 entry is among the five judges' winners. (#1-#9: 6 of 9 jams.)
- **Q4.** At least one winner ranks below 20th. (#1-#9: 6 of 9 jams.)
- **Q5.** itch.io's few-ratings adjustment pushes at least one entry from the raw top 10 out of the top 10.
  (#1-#9: 7 of 9 jams.)
- **Q6.** The fewest ratings any placed winner has is at least 5. (#1-#9: fewest 9.)

MV2's own entry
- **M1.** MV2's entry ends with fewer ratings than the jam's median and is not a judges' winner. MV2 does not
  rate other entries to attract ratings, so on #1-#9 counts it is unlikely to reach the median. This is
  stated so the result cannot be read selectively; if his entry does win, that is reported as M1 failing.

## Limits

One jam, five winners: each prediction is a single yes/no. Ratings are read after the jam, not when the
judges chose. A judges' pick can be a "hidden gem" by the rules, which Q4 expects at times.
