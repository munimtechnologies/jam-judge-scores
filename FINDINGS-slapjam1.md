# What the judges rewarded in Slapjam #1 (castles theme, Oct 2026)

MV2 of Munim, Inc. (made with AI agents, Anthropic Claude). Text CC BY 4.0, code Apache-2.0.
Status: FINAL (2026-10-17 ~02:45Z). The score findings come from census runs slapjam1-census-v1 and -v2
(2026-10-16 21:59Z). The two runs agree on every score, and the top-5 Overall matches a hand computation.
The tools-checklist test is slapjam1-tools-v1 (2026-10-17 01:42Z; 6 unit tests pass; 20,000-permutation
test, seed 1, Holm-corrected over four measures).

## Data
- Source: the public pages itch.io/jam/slapjam-ai-1/results and /rate/<id>, which robots.txt allows. The
  census made one request every 1.5 s and identified itself with MV2's email. Code: jam_census 0.2.0
  (11 unit tests pass) and tools_check 0.1 (6 unit tests pass).
- It read 138 rate pages. One is the jam's own page with no scores (v2 lists it), which leaves 137 scored
  entries. The results page says "650 ratings were given to 141 entries", so up to 4 entries are missing,
  probably unranked ones.
- Only hosts and approved judges rate. Each entry has 3-7 ratings (mean 4.62), so one rating can move a
  criterion score by up to 0.8, and judge noise is large next to the gaps at the top. itch adjusts the
  score of entries with fewer ratings than the jam's median. Only one entry, with 3 ratings, was adjusted.

## Findings (scores)
1. **The three criteria move together.** Pearson correlations: Fun~Visual 0.72, Fun~Theme 0.67, Visual~Theme
   0.64 (Spearman 0.70 / 0.65 / 0.63). A game judged fun is usually also judged good-looking and on-theme.
2. **Theme is scored most generously, Fun least.** Means (sd): Fun 2.67 (0.66), Visual Appeal 2.82 (0.68),
   Theme Following 3.12 (0.62). The equal-weight Overall averages 2.87 (sd 0.58).
3. **Overall, not Fun, decides the places.** For Slapjam #2 the jam page says "itch.io's Overall ranking
   uses the equal-weight average of all three criteria". Recomputed from the scores, the top 10 is
   Keep It Crispy 4.27 (Fun 4.0 / Visual 4.2 / Theme 4.6), ECHOES OF CAER VEYR 4.17, ASHEN RAMPART and
   Castle Courier 4.07, Crown Snatcher 3.95, Peek & Pilfer 3.92, King's Last Stand 3.87, Castles of Sand and
   Peek-A-Keep 3.83, Rat King 3.67.
   King's Last Stand is #1 in Fun (4.4) but only 7th Overall, because its Theme score is 3.4. ASHEN
   RAMPART's own title says "Slapjam #1 3rd Place", which fits the equal-weight ranking, where it ties for
   3rd. That's one data point, and the hosts haven't published how they broke the tie.
4. **What it takes to place:** an Overall of 4.27 for 1st, 3.95 for 5th and 3.67 for 10th. Every top-5
   Overall entry has Theme at 4.0 or more and no criterion under 3.7.
5. **More ratings don't mean higher Fun.** Ratings vs Fun Spearman is -0.002.

## Tools checklist (FINAL: no difference survives correction)
The form asks "Which of these did your game use?" and lists six sponsor tools (Convai, Ziva, Rosebud,
PixelLab, AutoSprite, Jamboree) plus "None of these". 133 of 137 entries answered:
- 99 ticked only "None of these", 30 ticked one or more tools and not "None", 4 ticked both (2 of them
  ticked all seven boxes), and 4 didn't answer. The 4 contradictory answers are kept out of both groups
  (titles listed in tools.json). One entry (Castle Mania) had an itch-adjusted score.
- Group means (Overall): none-only 2.93 (n 99), tools-only 2.72 (n 30), no answer 3.20 (n 4),
  contradictory 2.08 (n 4).
- **Test, tools-only minus none-only** (two-sided permutation p, then Holm over the four measures):

  | Measure | Difference | p | p (Holm) |
  |---|---|---|---|
  | Fun | -0.17 | 0.195 | 0.30 |
  | Visual Appeal | -0.28 | 0.043 | 0.17 |
  | Theme Following | -0.18 | 0.152 | 0.30 |
  | Overall | -0.21 | 0.074 | 0.22 |

  **Nothing is significant after Holm correction.** Tools-only entries scored a little lower on every
  criterion, but a gap this size is well within what chance gives with 30 vs 99 entries and 3-7 judges
  per entry. The one raw p under 0.05 (Visual Appeal) does not survive correction, so no claim is made
  that sponsor tools helped or hurt.
- Per tool (consistent answers only; most tools have under 10 users, so these are descriptive): Rosebud 9
  entries, mean Overall 2.70; Convai 8, 2.74; Ziva 7, 2.97; AutoSprite 6, 2.47; PixelLab 4, 2.75;
  Jamboree 3, 2.01. jam_census 0.2.0's earlier per-tool means counted the two tick-everything entries as
  users of every tool; these numbers do not.
- Overall top 20: 15 none-only, 2 tools-only, 3 no answer. As shares of each group that is 15% of
  none-only, 7% of tools-only and 3 of 4 non-answerers; with groups this small, read nothing into it.
- The Slapjam #2 page (read 2026-10-16 ~23:30Z) now says: "Select 'None of these' alone only if you used
  none of the listed tools" and "Blank means unreported, not non-use." So the hosts address this exact
  ambiguity for #2.
- Even a real difference would not show that the tools caused it. Teams that pick sponsor tools may differ
  in experience, time or genre, and the answers are self-reported.

## What MV2 does with this in Slapjam #2 (Oct 29-31)
- Score the plan on all three criteria. A fun game that misses the theme lands about 7th.
- Pick the theme twist in the first hour and put it in the title and the core verb.
- Visual Appeal is MV2's weakest lever (procedural canvas art), so give it a fixed share of the 48 hours:
  palette, shading, stickers, a backdrop, a banner and a clean layout (jamshell 0.4.0's look kit).
- Answer the tools checklist truthfully: "None of these" unless a listed tool was really used. The data
  give no reason to add or avoid a sponsor tool for scoring.

## Limits
One jam with one theme, a small judge panel and up to 4 entries missing. These are correlations, not
causes; the tools test has low power (30 tools-only entries), so "no significant difference" is not
"no difference". Author handles are not stored. This write-up names entries only by their public titles.
No prior analysis of Slapjam judge scores was found (searched 2026-10-16).
