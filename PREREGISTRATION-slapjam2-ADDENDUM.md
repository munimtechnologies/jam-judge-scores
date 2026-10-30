# Addendum to the Slapjam #2 pre-registration (dated 2026-10-30)

MV2 of Munim, Inc. (made with AI agents, Anthropic Claude). Text CC BY 4.0.
Written 2026-10-30 at about 14:45 UTC, while Slapjam #2 submissions are still open (they close 2026-10-31
15:00 UTC) and before any judge score is public (judging ends 2026-11-07 15:00 UTC). The git commit that adds
this file is its public timestamp.

## What changes
[PREREGISTRATION-slapjam2.md](PREREGISTRATION-slapjam2.md) says MV2 enters Slapjam #2 himself and that a
sensitivity run leaves out "his entry". Slapjam #2's FAQ allows more than one entry per person, each judged on
its own, and MV2 has made a second game in the jam window. So the sensitivity run now leaves out BOTH of his
titles:

```
python grade_prereg.py --csv out/entries.csv --out out/sens --exclude-title "Rush Order" --exclude-title "Nova Slingshot"
```

(`--exclude-title` can be given more than once.) If "Nova Slingshot" does not appear in the final entries list,
that flag simply excludes nothing; this will be said in the results.

## What does not change
Every prediction (H0-H8), every threshold, the core claim (H1, H2, H4 and H5 together), the data source, the
permutation count and seed, and the rule that the primary analysis includes every entry and stands if the two
runs disagree. H0's range (50 to 145 scored entries) is unchanged, although one of the counted entries may now
be MV2's second game.
