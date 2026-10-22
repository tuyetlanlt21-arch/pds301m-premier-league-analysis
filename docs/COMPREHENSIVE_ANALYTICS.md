# Comprehensive Analytics — Dashboard Data Contract

This extension is additive and leaves the existing PDS301m RQ1–RQ5 charts and report unchanged.

## Run

From the repository root after installing existing requirements:

```bash
python -c "from src.data_pipeline import load_raw_csvs, clean_matches; from src.team_analytics import export_dashboard_data; raw,_=load_raw_csvs('data/raw'); clean,_=clean_matches(raw); print(export_dashboard_data(clean))"
python -m unittest discover -s tests
```

Outputs in `data/dashboard/`: `team_matches.csv`, `team_summary.csv`, `team_venue_summary.csv`, `season_summary.csv`, `dashboard.json`. Generated outputs should be rebuilt after raw CSV changes.

## Dashboard sections

1. Overview: matches, teams, goals per match, home/draw/away result shares by season.
2. Results: wins, draws, losses, points per match, win/loss rates and goal difference.
3. Attack: goals, shots, shots on target, shot accuracy and shot conversion.
4. Defense: conceded goals, conceded goals per match, clean sheets and heavy defeats.
5. Home vs away: venue-specific team summary, using the same denominators.
6. Match dynamics: halftime deficit recoveries (win/draw), leads not converted to wins.
7. Efficiency: losses despite outshooting the opponent, mean shots in wins.
8. Form and consistency: five most recent completed matches, longest W/L streaks, population standard deviation of per-match goal difference.
9. Team comparison: compare any two team-season summaries; head-to-head match details are available via `head_to_head`.
10. Season trends: team and league comparisons across seasons.

## Metric definitions and cautions

- One completed fixture yields two team-perspective rows; **do not** use team-match row count as match count.
- Rates are percentages except points per match, mean margins and standard deviations.
- Comeback success: wins or draws when trailing at halftime / matches trailing at halftime. When the denominator is zero, report N/A.
- Lost lead: draws or losses after leading at halftime / matches leading at halftime.
- Loss despite more shots: losses when outshooting the opponent / matches when outshooting the opponent. This is descriptive, not a causal explanation.
- Shot accuracy: sum shots on target / sum shots; shot conversion: goals in matches with available shot data / sum shots. For reliable interpretation, apply a consistent eligible-match mask to shots and shots-on-target when both are required.
- Missing halftime or shot observations must be excluded, never treated as zero.
- A higher goal-difference standard deviation indicates greater variation in match margins, **not** necessarily worse performance.
- Last-five form requires sorting by date; equal-date fixtures use their original match order.
- A season with incomplete fixtures must be labeled partial. Comparing totals across partial and complete seasons is misleading; prefer per-match rates.
- Team ranking by points in this extension is descriptive; official league tables can differ due to deductions and tie-break rules.
- Data represent offline saved CSV snapshots, not live results or predictions.

## Website integration

The future React application should load `dashboard.json`, filter team-match records by season, team and venue, and recompute only metrics whose denominator is affected by the filter. Prefer precomputed team/season tables for default rankings. Keep a methodology/coverage panel visible.
