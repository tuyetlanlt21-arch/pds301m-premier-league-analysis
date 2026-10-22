# Expanded analytics pipeline

Run `py -m scripts.generate_analytics` from the repository root. It reads the
saved CSVs in `data/raw/`, cleans completed fixtures, normalizes team aliases,
derives one row per team per match, writes the dashboard contract under
`data/processed/analytics/`, and creates four expanded charts in `charts/`.

## Data contract

`cleaned_matches` contains one row per unique completed fixture. `team_match`
contains exactly two rows per fixture and is the canonical source for all team
metrics. Team results use `H`, `D`, `A` from the team's perspective; points use
the 3-1-0 rule. Dates are parsed as pandas datetimes in memory and are written
as ISO strings in CSV/JSON exports.

The generated tables include team-season, home/away, attacking, defensive,
winning/losing patterns, form/consistency, half-time/full-time dynamics, goal
distribution, and season summary tables. Percentages use the relevant observed
denominator. If an optional statistic is unavailable, its values remain null;
no missing observation is silently converted to zero. A zero denominator
produces null (`NaN` in pandas, `null` in JSON).

The current local input contains three seasons and 1,140 completed fixtures;
the generated season table determines completeness from observed fixtures and
participating teams rather than assuming a fixed season range. Volatility is the
standard deviation of match goal difference, not a standalone measure of team
quality. Pearson correlations describe association only and do not establish
causation.

Run `py -m pytest -q` or `py -m unittest discover -s tests -v`. The expanded
tests cover two-perspective row construction, points, missing optional data,
filtering, head-to-head direction, and CSV/JSON row-count consistency.
