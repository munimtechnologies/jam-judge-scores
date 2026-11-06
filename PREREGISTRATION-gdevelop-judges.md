# Pre-registration: where GDevelop's judges found their cash winners (BIG Game Jams #1-#9)

By MV2 of Munim, Inc. (mv2@munimtech.com). Written by AI agents (Anthropic Claude) working in his name.
Committed on 2026-11-06, before the data run (`gdjudges-v3`) that reads the nine jams' full results.
Text CC BY 4.0, code Apache-2.0.

## Question

GDevelop's BIG Game Jams pay cash only to five Judges' Award winners per jam. The organisers write that
judges "look at the community's highest rated games", plus perhaps a hidden gem. itch.io ranks a jam
by the community's ratings, and scales down the score of any entry that has fewer ratings than the
jam's median number of ratings. So an entry's ratings count may decide whether judges ever see it.

How far down the community ranking did the judges of jams #1-#9 reach for their 45 cash winners, and
did they ever pick an entry with fewer ratings than the jam's median?

## Data and method (frozen in this commit)

- `gdevelop-judges/judge_picks.csv`: the 45 Judges' Award winners, five per jam, with titles copied
  by hand from GDevelop's own winner posts (blog URL on each row).
- `gdevelop-judges/judge_reach.py` (0.2, with test file): reads every page of each jam's public itch.io
  results (`itch.io/jam/<slug>/results`), records each ranked entry's Overall rank, score, raw score and
  ratings count ("Ranked 2nd with 68 ratings"), and matches each winner by title (exact, then
  unambiguous prefix). It writes `picks.csv`, `jams.csv` and `summary.json`.
- Rank = the Overall rank itch.io shows (after its few-ratings adjustment). Raw rank = 1 + the number
  of ranked entries in that jam with a strictly higher raw Overall score. Jam median ratings = the
  median ratings count over all ranked entries of that jam.
- Unmatched winners: before grading, a title may be fixed by hand only by choosing one of the
  `candidates` the script lists, and every such fix is reported. If fewer than 40 of 45 winners can
  be matched, the core predictions are reported as not gradable.

## What is already known (so not predicted)

- GDevelop's blog posts list each jam's community top 10 next to the judges' picks. From them, 25 of
  the 45 cash winners were in their jam's community top 10 and 20 were not. The run is expected to
  reproduce that (a data check, not a prediction).
- Hand checks made on 2026-11-06 while fixing the parser: jam #9 (median 13 ratings by an earlier
  count; its top 10 had 13 to 68 ratings): Cheese The Skies 1st with 19 ratings, Illegal Fat Gambling
  2nd with 68, Save Kitt 3rd with 31, Kilimanjaro 20th with 43; jam #1: Hero Builder 1st with 94.
  Jam #6 lists 85 entries with a median of 8 ratings.
- An earlier run of the reader (0.1, 2026-11-06) read 2,285 ranked entries across the nine jams but,
  because of a parser bug, matched none of the winners and recorded no ratings counts.
- Nothing else about the other 40 winners' ranks or ratings counts has been read.

## Predictions

Core (all three must hold for "held"):

- **P1.** At least 85% of the matched winners rank in the top 30 of their jam's Overall ranking.
- **P2.** Fewer than 20% of the matched winners have fewer ratings than their jam's median.
- **P3.** In at least 6 of the 9 jams, at least one entry in the raw-score top 10 is pushed out of the
  Overall top 10 by the few-ratings adjustment (`raw_top_displaced` >= 1).

Secondary:

- **P4.** No matched winner ranks worse than 60th.
- **P5.** The median rank of the matched winners is 10 or better.
- **P6.** Every matched winner has at least 5 ratings.

## Why it matters

MV2 does not rate other entries, so his entries tend to get fewer ratings than a jam's median. If P2
holds, a below-median entry almost never receives a judges' prize in these jams, and getting a game
in front of enough raters is part of winning, not an extra. If P2 fails, judges do reach entries the
community ranking buries.

## Limits

Titles come from blog posts and may differ from itch.io titles; entries deleted since a jam ended are
missing from its results; results pages show the counts as they are today, not as the judges saw them;
nine jams by one organiser are not all jams.
