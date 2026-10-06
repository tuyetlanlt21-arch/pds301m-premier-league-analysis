# P6 Mini Report — Premier League Match Analysis

**Dataset:** 1,140 completed matches across 2023/24, 2024/25, 2025/26.

## Project overview and questions

This project examines whether outcomes differ by home/away venue, which teams scored and shot most, how half-time results relate to full-time results, how goals are distributed, and how match statistics relate to one another. These are descriptive questions; the project does not claim causal effects or validated predictions.

## Data and method

Match-level CSV files were collected from [Football-Data.co.uk](https://www.football-data.co.uk/englandm.php) and read from `data/raw/`. Season context is linked from the [Premier League seasons list](https://en.wikipedia.org/wiki/List_of_Premier_League_seasons); it is not used as match-level data. The reusable pipeline checks raw rows, parses dates and numeric columns, retains completed matches with valid full-time scores, removes duplicate fixtures, and derives result and match-total features. Missing optional statistics remain missing rather than being filled with zero.

Pandas groups match outcomes, teams, seasons, and statistics; NumPy summarizes goal totals; reusable functions in `src/analysis.py` generate the figures. Correlations are Pearson associations and do not imply that one statistic causes another.

## Findings

- **Home advantage:** home wins were 43.2%, draws 24.5%, and away wins 32.4% of completed matches.
- **Team performance:** **Man City** scored the most goals (245). Liverpool led in shots (2,026); Man City led in shots on target (700).
- **Half-time to full-time:** The most frequent half-time to full-time transition was **Home win → Home win** (300 matches).
- **Goals:** mean 2.99, median 3.0 total goals per match. 2023/24 had the highest seasonal mean (3.28).
- **Match statistics:** The strongest pairwise correlation was between Total shots and Shots on target (Pearson r = 0.61). Across matches with shot data, total shots and total goals had Pearson r = 0.22.

## Visualizations

The notebook and T13 code create an outcome bar chart, team-scoring bar chart, half-time/full-time heatmap, goal histogram, season box plot, match-statistic correlation heatmap, goals-versus-shots scatter plot, and season comparison chart. Each PNG includes a short data-backed insight; the companion `charts/insights.md` summarizes them.

| Figure | Research question |
|---|---|
| `home_advantage_outcomes.png` | RQ1 |
| `top_scoring_teams.png` | RQ2 |
| `halftime_fulltime_heatmap.png` | RQ3 |
| `goal_distribution_histogram.png`, `goal_distribution_by_season_boxplot.png` | RQ4 |
| `match_statistics_correlation_heatmap.png`, `goals_vs_shots_scatter.png` | RQ5 |
| `season_average_goals.png` | Season comparison |

## Limitations and contributions

The findings cover only the local CSV seasons and completed matches. Optional statistics may be missing, team totals depend on appearances, and source snapshots may change. The analysis is descriptive, not a causal study or validated prediction model.

| Student ID | Team member | Contribution |
|---|---|---|
| SE203600 | Lê Thị Tuyết Lan |  |
| SE180021 | Nguyễn Hoàng Thùy Linh |  |
| SE203216 | Trần Long Vân |  |
| SE190537 | Nguyễn Quốc Toàn |  |

## Conclusion

The combined tables and charts provide evidence for the five project questions within the seasons analyzed. Interpret the results as patterns in those observed matches; do not generalize beyond the available data without further seasons and validation.
