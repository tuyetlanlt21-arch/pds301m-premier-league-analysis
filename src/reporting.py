"""Create a concise, data-backed P6 mini report from the analysis outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


CHART_FILES = [
    "home_advantage_outcomes.png",
    "top_scoring_teams.png",
    "halftime_fulltime_heatmap.png",
    "goal_distribution_histogram.png",
    "goal_distribution_by_season_boxplot.png",
    "match_statistics_correlation_heatmap.png",
    "goals_vs_shots_scatter.png",
    "season_average_goals.png",
]


def _team_summary(matches: pd.DataFrame) -> pd.DataFrame:
    home = pd.DataFrame({"Team": matches["HomeTeam"], "Goals": matches["FTHG"]})
    away = pd.DataFrame({"Team": matches["AwayTeam"], "Goals": matches["FTAG"]})
    for stat, home_column, away_column in (("Shots", "HS", "AS"), ("Shots on target", "HST", "AST")):
        if {home_column, away_column}.issubset(matches.columns):
            home[stat] = matches[home_column]
            away[stat] = matches[away_column]
    combined = pd.concat([home, away], ignore_index=True)
    summary = combined.groupby("Team").agg(Appearances=("Team", "size"))
    for column in combined.columns:
        if column != "Team":
            summary[column] = combined.groupby("Team")[column].sum(min_count=1)
    summary["Goals per appearance"] = summary["Goals"] / summary["Appearances"]
    return summary.sort_values("Goals", ascending=False)


def render_final_report(matches: pd.DataFrame, summaries: dict[str, object]) -> str:
    """Render 1–2 page Markdown report using current cleaned match data."""
    seasons = sorted(matches["Season"].astype(str).unique())
    outcome = summaries["home_advantage"]
    transitions = summaries["halftime_fulltime"]
    season_summary = summaries["season_comparison"]
    correlations = summaries["match_statistics_correlation"]
    scatter = summaries["goals_vs_shots"]
    team_summary = _team_summary(matches)

    top_team = team_summary.index[0]
    total_goal_mean = float(matches["total_goals"].mean())
    total_goal_median = float(matches["total_goals"].median())
    home_share = float(outcome.get("Home win", 0))
    draw_share = float(outcome.get("Draw", 0))
    away_share = float(outcome.get("Away win", 0))

    if transitions.to_numpy().sum():
        transition = transitions.stack().idxmax()
        transition_text = (
            f"The most frequent half-time to full-time transition was **{transition[0]} → {transition[1]}** "
            f"({int(transitions.loc[transition[0], transition[1]]):,} matches)."
        )
    else:
        transition_text = "Half-time result data were unavailable, so transitions could not be summarized."

    best_season = season_summary.sort_values("MeanGoals", ascending=False).iloc[0]
    correlation_pairs = [
        (float(correlations.loc[a, b]), a, b)
        for i, a in enumerate(correlations.columns)
        for b in correlations.columns[i + 1 :]
        if pd.notna(correlations.loc[a, b])
    ]
    if correlation_pairs:
        corr, stat_a, stat_b = max(correlation_pairs, key=lambda item: abs(item[0]))
        corr_text = f"The strongest pairwise correlation was between {stat_a} and {stat_b} (Pearson r = {corr:.2f})."
    else:
        corr_text = "Available match-statistic values did not support a pairwise correlation estimate."
    shot_goal_corr = scatter["Total shots"].corr(scatter["Total goals"])
    if pd.notna(shot_goal_corr):
        scatter_text = f"Across matches with shot data, total shots and total goals had Pearson r = {shot_goal_corr:.2f}."
    else:
        scatter_text = "There were not enough complete shot totals to estimate a shots-goals correlation."

    available_stats = [
        column for column in ("Shots", "Shots on target")
        if column in team_summary.columns and team_summary[column].notna().any()
    ]
    attack_details = []
    for column in available_stats:
        leader = team_summary[column].idxmax()
        attack_details.append(f"{leader} led in {column.lower()} ({team_summary.loc[leader, column]:,.0f})")
    attack_text = f"**{top_team}** scored the most goals ({team_summary.loc[top_team, 'Goals']:,.0f})."
    if attack_details:
        attack_text += " " + "; ".join(attack_details) + "."
    else:
        attack_text += " Shot totals were unavailable or incomplete."

    lines = [
        "# P6 Mini Report — Premier League Match Analysis",
        "",
        f"**Dataset:** {len(matches):,} completed matches across {', '.join(seasons)}.",
        "",
        "## Project overview and questions",
        "",
        "This project examines whether outcomes differ by home/away venue, which teams scored and shot most, how half-time results relate to full-time results, how goals are distributed, and how match statistics relate to one another. These are descriptive questions; the project does not claim causal effects or validated predictions.",
        "",
        "## Data and method",
        "",
        "Match-level CSV files were collected from [Football-Data.co.uk](https://www.football-data.co.uk/englandm.php) and read from `data/raw/`. Season context is linked from the [Premier League seasons list](https://en.wikipedia.org/wiki/List_of_Premier_League_seasons); it is not used as match-level data. The reusable pipeline checks raw rows, parses dates and numeric columns, retains completed matches with valid full-time scores, removes duplicate fixtures, and derives result and match-total features. Missing optional statistics remain missing rather than being filled with zero.",
        "",
        "Pandas groups match outcomes, teams, seasons, and statistics; NumPy summarizes goal totals; reusable functions in `src/analysis.py` generate the figures. Correlations are Pearson associations and do not imply that one statistic causes another.",
        "",
        "## Findings",
        "",
        f"- **Home advantage:** home wins were {home_share:.1f}%, draws {draw_share:.1f}%, and away wins {away_share:.1f}% of completed matches.",
        f"- **Team performance:** {attack_text}",
        f"- **Half-time to full-time:** {transition_text}",
        f"- **Goals:** mean {total_goal_mean:.2f}, median {total_goal_median:.1f} total goals per match. {best_season['Season']} had the highest seasonal mean ({best_season['MeanGoals']:.2f}).",
        f"- **Match statistics:** {corr_text} {scatter_text}",
        "",
        "## Visualizations",
        "",
        "The notebook and T13 code create an outcome bar chart, team-scoring bar chart, half-time/full-time heatmap, goal histogram, season box plot, match-statistic correlation heatmap, goals-versus-shots scatter plot, and season comparison chart. Each PNG includes a short data-backed insight; the companion `charts/insights.md` summarizes them.",
        "",
        "| Figure | Research question |",
        "|---|---|",
        "| `home_advantage_outcomes.png` | RQ1 |",
        "| `top_scoring_teams.png` | RQ2 |",
        "| `halftime_fulltime_heatmap.png` | RQ3 |",
        "| `goal_distribution_histogram.png`, `goal_distribution_by_season_boxplot.png` | RQ4 |",
        "| `match_statistics_correlation_heatmap.png`, `goals_vs_shots_scatter.png` | RQ5 |",
        "| `season_average_goals.png` | Season comparison |",
        "",
        "## Limitations and contributions",
        "",
        "The findings cover only the local CSV seasons and completed matches. Optional statistics may be missing, team totals depend on appearances, and source snapshots may change. The analysis is descriptive, not a causal study or validated prediction model.",
        "",
        "| Student ID | Team member | Contribution |",
        "|---|---|---|",
        "| SE203600 | Lê Thị Tuyết Lan |  |",
        "| SE180021 | Nguyễn Hoàng Thùy Linh |  |",
        "| SE203216 | Trần Long Vân |  |",
        "| SE190537 | Nguyễn Quốc Toàn |  |",
        "",
        "## Conclusion",
        "",
        "The combined tables and charts provide evidence for the five project questions within the seasons analyzed. Interpret the results as patterns in those observed matches; do not generalize beyond the available data without further seasons and validation.",
        "",
    ]
    return "\n".join(lines)


def write_final_report(matches: pd.DataFrame, summaries: dict[str, object], output_path: str | Path) -> Path:
    """Write the rendered report to the requested path and return that path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_final_report(matches, summaries), encoding="utf-8")
    return path
