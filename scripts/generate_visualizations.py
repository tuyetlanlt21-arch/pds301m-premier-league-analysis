"""Run the T13 chart suite against every raw season CSV in data/raw/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import generate_all_visualizations


ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT / "data" / "raw"
CHARTS_DIR = ROOT / "charts"


def load_completed_matches() -> pd.DataFrame:
    """Load, validate, clean, normalize, and combine all collected seasons."""
    from src.data_pipeline import clean_matches, create_features, load_raw_csvs

    raw, paths = load_raw_csvs(RAW_DATA_DIR)
    clean, counts = clean_matches(raw)
    print(f"Loaded {len(paths)} season CSV file(s)")
    print(f"Retained {counts['clean_rows']:,} completed matches after cleaning")
    if clean.empty:
        raise ValueError(f"No completed matches found in {RAW_DATA_DIR}.")
    return create_features(clean)


def write_visualization_insights(
    matches: pd.DataFrame, summaries: dict[str, object], output_dir: Path
) -> Path:
    """Write one concise, data-backed interpretation for every generated chart."""
    outcome = summaries["home_advantage"]
    teams = summaries["team_performance"]
    halftime = summaries["halftime_fulltime"]
    goals = summaries["goal_distribution"]
    by_season = summaries["goal_boxplot_data"]
    correlation = summaries["match_statistics_correlation"]
    scatter = summaries["goals_vs_shots"]
    season_summary = summaries["season_comparison"]

    assert isinstance(outcome, pd.Series)
    assert isinstance(teams, pd.Series)
    assert isinstance(halftime, pd.DataFrame)
    assert isinstance(goals, pd.Series)
    assert isinstance(by_season, pd.DataFrame)
    assert isinstance(correlation, pd.DataFrame)
    assert isinstance(scatter, pd.DataFrame)
    assert isinstance(season_summary, pd.DataFrame)

    total_matches = len(matches)
    home_share = float(outcome.get("Home win", 0))
    away_share = float(outcome.get("Away win", 0))
    difference = home_share - away_share
    outcome_insight = (
        f"Home wins were {home_share:.1f}% of completed matches, compared with "
        f"{away_share:.1f}% away wins (a {difference:+.1f} percentage-point difference)."
    )

    top_team, top_goals = teams.index[0], int(teams.iloc[0])
    transition = halftime.stack().idxmax()
    transition_count = int(halftime.loc[transition[0], transition[1]])
    transition_share = transition_count / total_matches * 100

    goal_counts = goals.value_counts()
    common_goal_total = int(goal_counts.index[0])
    common_goal_count = int(goal_counts.iloc[0])
    common_goal_share = common_goal_count / total_matches * 100

    medians = by_season.groupby("Season")["Total goals"].median().sort_values(ascending=False)
    median_season, median_goals = medians.index[0], float(medians.iloc[0])

    pairs = [
        (float(correlation.loc[a, b]), a, b)
        for i, a in enumerate(correlation.columns)
        for b in correlation.columns[i + 1 :]
        if pd.notna(correlation.loc[a, b])
    ]
    if pairs:
        strongest, stat_a, stat_b = max(pairs, key=lambda pair: abs(pair[0]))
        corr_insight = (
            f"The strongest pairwise correlation was between {stat_a} and {stat_b} "
            f"(Pearson r = {strongest:.2f}), a {('positive' if strongest >= 0 else 'negative')} association."
        )
    else:
        corr_insight = "There was not enough variation in the match statistics to calculate a pairwise correlation."

    shot_goal_corr = float(scatter["Total shots"].corr(scatter["Total goals"]))
    if pd.isna(shot_goal_corr):
        scatter_insight = "There was not enough variation in total shots or goals to estimate their correlation."
    else:
        direction = "positive" if shot_goal_corr >= 0 else "negative"
        scatter_insight = f"Total shots and total goals had a {direction} Pearson correlation (r = {shot_goal_corr:.2f})."

    top_season = season_summary.sort_values("MeanGoals", ascending=False).iloc[0]
    season_insight = (
        f"{top_season['Season']} had the highest average, at {top_season['MeanGoals']:.2f} goals per match "
        f"across {int(top_season['Matches'])} completed matches."
    )

    entries = [
        ("home_advantage_outcomes.png", "RQ1 — Match outcomes", outcome_insight),
        ("top_scoring_teams.png", "RQ2 — Team attacking performance", f"{top_team} scored the most goals across the included seasons: {top_goals:,} in total."),
        ("halftime_fulltime_heatmap.png", "RQ3 — Half-time to full-time", f"The most frequent transition was {transition[0]} → {transition[1]}: {transition_count:,} matches ({transition_share:.1f}%)."),
        ("goal_distribution_histogram.png", "RQ4 — Goal distribution", f"The most common match total was {common_goal_total} goals, occurring in {common_goal_count:,} matches ({common_goal_share:.1f}%)."),
        ("goal_distribution_by_season_boxplot.png", "RQ4 — Goal spread by season", f"{median_season} had the highest median total goals per match ({median_goals:.1f})."),
        ("match_statistics_correlation_heatmap.png", "RQ5 — Match-statistic correlations", corr_insight),
        ("goals_vs_shots_scatter.png", "RQ5 — Shots and goals", scatter_insight),
        ("season_average_goals.png", "Season comparison", season_insight),
    ]

    lines = [
        "# T13 — Visualization insights",
        "",
        f"Based on {total_matches:,} completed matches from {', '.join(sorted(matches['Season'].astype(str).unique()))}.",
        "Each note describes the values shown in the chart; correlations are associations and do not establish cause.",
        "",
    ]
    for filename, heading, insight in entries:
        lines.extend([f"## {heading}", "", f"![{heading}]({filename})", "", f"**Evidence-based insight:** {insight}", ""])

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "insights.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    matches = load_completed_matches()
    summaries = generate_all_visualizations(matches, CHARTS_DIR)
    insights_path = write_visualization_insights(matches, summaries, CHARTS_DIR)
    print(f"\nGenerated {len(list(CHARTS_DIR.glob('*.png')))} charts in {CHARTS_DIR.relative_to(ROOT)}:")
    for chart in sorted(CHARTS_DIR.glob("*.png")):
        print(f"  - {chart.name}")
    print(f"\nSeasons analyzed: {', '.join(sorted(matches['Season'].astype(str).unique()))}")
    print(f"Completed matches: {len(matches):,}")
    print("Home/Draw/Away outcome shares (%):")
    print(summaries["home_advantage"].round(1).to_string())
    print(f"\nEvidence-based notes saved in {insights_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
