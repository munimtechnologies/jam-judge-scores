# jam-judge-scores

What do game jam judges reward? This repo holds an open census of judge scores from itch.io jams, findings
from Slapjam #1, and pre-registered tests of whether those findings hold in Slapjam #2 and thatgamejam #02.

By MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents (Anthropic Claude) working in his name.
Code Apache-2.0 (see LICENSE); text and data CC BY 4.0.

## Contents
- `FINDINGS-slapjam1.md`: what the judges rewarded in Slapjam #1, a jam where AI use is required (137
  judge-scored entries). The three criteria move together (Pearson 0.64-0.72), Theme is scored most
  generously, and the most fun game placed only about 7th because of a weak Theme score. Entries that
  ticked sponsor tools showed no significant score difference. Also posted as a devlog:
  https://munimv2.itch.io/jamshell/devlog/1711816/what-the-judges-rewarded-in-slapjam-1
- `PREREGISTRATION-slapjam2.md`: nine predictions for Slapjam #2 (Oct 29-31, 2026), written and committed
  before the jam opened. Graded after judging ends on Nov 7, 2026, whatever the outcome.
- `PREREGISTRATION-thatgamejam02.md`: eight predictions for thatgamejam #02 (thatgamecompany's jam; $10,000),
  written on Oct 30, 2026, before submissions close (Nov 8) and before any voting. They test whether
  thatgamecompany's own picks again sit high in the community ranking (20 of 22 placings did so in its two
  earlier jams), whether browser games again get more ratings, and whether disclosing AI again shows no score
  cost. Graded after the winners are announced on Dec 22, 2026, whatever the outcome.
- `jam_census.py`: reads a jam's public results and rate pages (one request every 1.5 s; no author handles
  kept) and writes entries.csv and summary.json.
- `jam_picks.py`: the same for jams with hand-picked awards, plus each entry's game page (browser play,
  itch's AI-disclosure field, team size); used for thatgamejam #01 and #02.
- `tools_check.py`: permutation test of tools-checklist answers vs scores, with Holm correction.
- `grade_prereg.py`: grades the Slapjam #2 predictions from an entries.csv.
- `grade_tgj02.py`: grades the thatgamejam #02 predictions from jam_picks.py's entries.csv.
- `data/slapjam-ai-1/entries.csv`: the Slapjam #1 census (public game titles, scores, rating counts and
  tools-checklist answers).

## Run
Python 3.10+ and the standard library only.

    python -m unittest discover
    python jam_census.py --jam slapjam-ai-2 --out out/
    python grade_prereg.py --csv out/entries.csv --out out/
    python jam_picks.py --jam thatgamejam02 --out out/tgj02 --delay 2.5
    python grade_tgj02.py --csv out/tgj02/entries.csv --out out/tgj02-grade

## Limits
Judge panels are small (3-7 ratings per entry in Slapjam), so one judge can move a score by up to 0.8, and
thatgamejam #02 has only three judged winners. These are patterns, not causes. Scores are as itch.io shows
them, including its adjustment for entries with fewer ratings than the jam's median.
