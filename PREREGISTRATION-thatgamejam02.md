# Pre-registration: thatgamecompany's judges and the community in thatgamejam #02

Written 2026-10-30 by AI agents (Anthropic Claude) working in the name of MV2 of Munim, Inc., while thatgamejam
#02 is still open for submissions (it closes 2026-11-08 07:59 UTC; community voting runs Nov 8 - Dec 11 PT;
winners are announced Dec 22). No #02 entry, rating or result could be seen when this was written.
Code: `grade_tgj02.py` (Apache-2.0) with its tests; census: `jam_picks.py` 0.2.0. Text CC BY 4.0.

Disclosure: MV2 has his own game in this jam (Lantern Drift). None of the predictions is about it, and every
prediction is graded twice: on all entries, and again without his entry (`--exclude-title "Lantern Drift"`).

## What we already know (from two earlier thatgamecompany jams, read in October 2026)
| | thatgamejam #01 | tgc x Coreblazer |
|---|---|---|
| Entries ranked by the community | 244 | 253 |
| Hand-picked placings | 19 (4 awards, up to 5 places each) | 3 (one winner each) |
| Picks in the community's top half | 17 of 19 | 3 of 3 |
| Picks in the top 10% | 8 of 19 | 1 of 3 |
| Picks' mean community percentile | 0.225 | 0.251 |
| Best Overall winner(s)' community rank | #2 and #39 (1st places) | #8 |
| Community #1 also won Best Overall 1st place? | no (it placed 3rd) | no |
| Median ratings per entry; itch's implied median | 17; 17.0 | 6; 6.0 |
| Share ticking itch's AI disclosure | 71 of 242 (0.29) | 35 of 249 (0.14) |

Across both jams, 20 of 22 hand-picked placings sat in the community's top half. MV2's earlier studies of 10
itch.io jams found that browser-playable games get about twice the ratings, and found no clear rating cost to
disclosing AI (devlogs at https://munimv2.itch.io/jamshell/devlog).

#02 differs from #01: each prize has ONE winner (Best Overall $3,000, Best Gameplay $2,000, Best Visual Design
$2,000, Community's Voice $2,000 by community rating, TapTap's Choice $1,000), and the rules now say a game that
does not disclose AI use in its description is disqualified.

## Predictions (fixed now; graded after Dec 22, 2026, whatever the result)
"Award winners" = the rank-1 games of Best Overall, Best Gameplay and Best Visual Design on itch's results
pages. A winner that is missing, or not in the Community's Voice ranking (e.g. a TapTap-only game), counts
AGAINST P1-P4. Percentile = community rank / number of entries ranked.

- **P1 (core):** all three award winners rank in the community's top half.
- **P2:** the Best Overall winner ranks in the community's top 10%.
- **P3 (core):** the three award winners' mean community percentile is at most 0.30.
- **P4:** the Best Overall winner is NOT the community's #1.
- **P5:** itch's rating-count adjustment uses the jam's median ratings per entry: the median rating count implied
  by the scaled-down entries is within 0.5 ratings of the real median.
- **P6:** at least 29% of the ranked entries tick itch's AI-disclosure field (the share in #01).
- **P7 (core):** browser-playable entries get at least 1.3 times the median ratings of download-only entries,
  and more ratings by a one-sided Mann-Whitney test at p < 0.05.
- **P8:** raw Community's Voice scores of entries that tick itch's AI field and entries that say no generative AI
  was used do NOT differ (two-sided Mann-Whitney p > 0.05).

Core = P1, P3, P7. TapTap's Choice is reported but not tested (it is judged by TapTap's team, and may go to a
game on TapTap only).

## Method
`python jam_picks.py --jam thatgamejam02 --out census --delay 2.5` reads only public itch.io pages (results
pages, each entry's rate page and its game page; one request every 2.5 s; a User-Agent naming MV2). Then
`python grade_tgj02.py --csv census/entries.csv --out primary` and the same with `--exclude-title "Lantern Drift"`.
Thresholds are constants in `grade_tgj02.py`, and a test pins them. If pages fail to load (itch rate-limits),
the census is re-run with a longer delay; the predictions and thresholds never change.

## Limits stated in advance
- Three judged winners: P1-P4 are about a tiny sample and can fail by chance. They test whether the earlier
  pattern repeats, not why it happens.
- itch's AI field is self-reported; "no generative AI" is a claim, not a check. P6 and P8 use the field only.
- Game pages may be edited after judging (platforms, descriptions).
- Judges may see things the community does not (e.g. TapTap builds).
