# T13 — Premier League Data Visualization

This implementation creates eight charts tied to the project's research questions:

| Research question | Chart | Output file |
| --- | --- | --- |
| RQ1: home advantage | Home/draw/away outcome shares | `home_advantage_outcomes.png` |
| RQ2: team attacking performance | Top 10 teams by goals | `top_scoring_teams.png` |
| RQ3: half-time vs full-time | Result transition heatmap | `halftime_fulltime_heatmap.png` |
| RQ4: goal distribution | Match-goal histogram and season box plot | `goal_distribution_histogram.png`, `goal_distribution_by_season_boxplot.png` |
| RQ5: match-statistic associations | Correlation heatmap and shots-vs-goals scatter plot | `match_statistics_correlation_heatmap.png`, `goals_vs_shots_scatter.png` |
| Additional comparison | Mean goals per completed match by season | `season_average_goals.png` |

The statistics heatmap uses goals, shots, shots on target, and corners. Those columns are part of the project's required data schema. It does not rely on fouls columns, which are not guaranteed by the project schema.

Each PNG also has a short insight line with a value calculated from the input matches. The run additionally writes `charts/insights.md`, which embeds the charts and gives the same findings in a report format.

## Install and run from the repository root

Install the project and notebook/visualization dependencies on Windows:

```powershell
py -m pip install -r requirements.txt
py -m pip install -r requirements-t14.txt
```

Then generate charts and insights:

```bash
py -m scripts.generate_visualizations
```

The script reads every CSV in `data/raw/`, validates and cleans each season with `src.data_pipeline`, removes unfinished matches, normalizes team names, and writes 300-DPI PNGs to `charts/`.

Run the focused tests with:

```bash
py -m unittest discover -s tests -v
```

## Files in this implementation

- `src/analysis.py`: chart functions and the `generate_all_visualizations` entry point.
- `scripts/generate_visualizations.py`: loads project raw files and runs the chart suite.
- `tests/test_analysis_visualizations.py`: verifies chart generation, outcome percentages, schema checks, and input immutability.
