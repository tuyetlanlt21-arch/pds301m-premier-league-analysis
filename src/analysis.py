"""Visualization functions for the Premier League match analysis project.

The functions accept the project's raw or feature-engineered match DataFrame,
save publication-ready PNGs, and return the values shown in the charts so they
can also be reported in the analysis notebook.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RESULT_ORDER = ["H", "D", "A"]
RESULT_LABELS = {"H": "Home win", "D": "Draw", "A": "Away win"}
SEASON_PALETTE = "viridis"


def _require_columns(data: pd.DataFrame, columns: set[str], chart_name: str) -> None:
    missing = sorted(columns - set(data.columns))
    if missing:
        raise ValueError(f"{chart_name} requires columns: {', '.join(missing)}")
    if data.empty:
        raise ValueError(f"{chart_name} cannot be created from an empty DataFrame.")


def _save(fig: plt.Figure, output_dir: str | Path, filename: str) -> Path:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / filename
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _add_insight(fig: plt.Figure, text: str) -> None:
    """Place a compact, data-backed takeaway in the chart's lower margin."""
    fig.text(
        0.01,
        0.015,
        f"Insight: {text}",
        ha="left",
        va="bottom",
        fontsize=8,
        color="#344054",
        wrap=True,
        bbox={"facecolor": "#f2f5f7", "edgecolor": "none", "boxstyle": "round,pad=0.45"},
    )


def _combined_stat(data: pd.DataFrame, home: str, away: str) -> pd.Series:
    return pd.to_numeric(data[home], errors="coerce") + pd.to_numeric(
        data[away], errors="coerce"
    )


def _result_codes(data: pd.DataFrame) -> pd.Series:
    column = "FTR" if "FTR" in data.columns else "result_label"
    if column not in data.columns:
        raise ValueError("Home-result chart requires either FTR or result_label.")
    values = data[column].astype("string").str.strip()
    labels = {
        "Home Win": "H", "Home win": "H", "Home": "H",
        "Draw": "D", "Away Win": "A", "Away win": "A", "Away": "A",
    }
    return values.replace(labels)


def analyze_home_advantage(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.Series:
    """RQ1: show the percentage of home wins, draws, and away wins."""
    _require_columns(data, set(), "Home-advantage chart")
    results = _result_codes(data)
    rates = (results.value_counts(normalize=True).reindex(RESULT_ORDER, fill_value=0) * 100)
    rates.index = [RESULT_LABELS[code] for code in RESULT_ORDER]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#16845b", "#d4a72c", "#3973ac"]
    bars = ax.bar(rates.index, rates.values, color=colors, width=0.65)
    ax.bar_label(bars, labels=[f"{value:.1f}%" for value in rates], padding=4)
    ax.set(title="Premier League match outcomes", ylabel="Share of completed matches (%)", xlabel="Full-time result")
    ax.set_ylim(0, max(10, float(rates.max()) * 1.18))
    ax.spines[["top", "right"]].set_visible(False)
    _add_insight(fig, f"Home wins were {rates['Home win']:.1f}% vs {rates['Away win']:.1f}% away wins.")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "home_advantage_outcomes.png")
    return rates


def analyze_team_performance(
    data: pd.DataFrame, output_dir: str | Path = "charts", top_n: int = 10
) -> pd.Series:
    """RQ2: compare total goals scored by each team across the included seasons."""
    _require_columns(data, {"HomeTeam", "AwayTeam", "FTHG", "FTAG"}, "Team-performance chart")
    home = pd.DataFrame({"Team": data["HomeTeam"], "Goals": pd.to_numeric(data["FTHG"], errors="coerce")})
    away = pd.DataFrame({"Team": data["AwayTeam"], "Goals": pd.to_numeric(data["FTAG"], errors="coerce")})
    totals = (
        pd.concat([home, away], ignore_index=True)
        .dropna(subset=["Team", "Goals"])
        .groupby("Team")["Goals"].sum(min_count=1)
        .sort_values(ascending=False)
    )
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")
    shown = totals.head(top_n).sort_values()

    fig, ax = plt.subplots(figsize=(10, max(5, 0.42 * len(shown))))
    bars = ax.barh(shown.index, shown.values, color=sns.color_palette("viridis", len(shown)))
    ax.bar_label(bars, padding=3, fmt="%.0f")
    ax.set(title=f"Top {min(top_n, len(totals))} teams by goals scored", xlabel="Goals", ylabel="Team")
    ax.spines[["top", "right"]].set_visible(False)
    _add_insight(fig, f"{totals.index[0]} scored the most goals ({totals.iloc[0]:,.0f}) in the included seasons.")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "top_scoring_teams.png")
    return totals


def analyze_goal_distribution(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.Series:
    """RQ4: plot the distribution of total goals per completed match."""
    _require_columns(data, {"FTHG", "FTAG"}, "Goal-distribution chart")
    goals = _combined_stat(data, "FTHG", "FTAG").dropna()
    if goals.empty:
        raise ValueError("Goal-distribution chart has no numeric goal totals.")

    upper = int(goals.max())
    bins = [value - 0.5 for value in range(upper + 2)]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(goals, bins=bins, color="#147d78", edgecolor="white", ax=ax)
    ax.set(title="Goals per match", xlabel="Total goals (home + away)", ylabel="Number of matches")
    ax.set_xticks(range(upper + 1))
    ax.spines[["top", "right"]].set_visible(False)
    mode = int(goals.value_counts().index[0])
    mode_count = int(goals.value_counts().iloc[0])
    _add_insight(fig, f"{mode} goals was the most common match total ({mode_count:,} matches).")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "goal_distribution_histogram.png")
    return goals.rename("total_goals")


def analyze_goal_boxplot(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.DataFrame:
    """RQ4: compare the spread of match goals by season with a box plot."""
    _require_columns(data, {"FTHG", "FTAG", "Season"}, "Season goal box plot")
    plot_data = data[["Season"]].copy()
    plot_data["Total goals"] = _combined_stat(data, "FTHG", "FTAG")
    plot_data = plot_data.dropna(subset=["Season", "Total goals"])
    if plot_data.empty:
        raise ValueError("Season goal box plot has no complete rows.")

    order = sorted(plot_data["Season"].astype(str).unique())
    plot_data["Season"] = plot_data["Season"].astype(str)
    fig, ax = plt.subplots(figsize=(max(8, len(order) * 1.5), 5))
    sns.boxplot(data=plot_data, x="Season", y="Total goals", order=order, color="#6baed6", ax=ax)
    ax.set(title="Match-goal distribution by season", xlabel="Season", ylabel="Total goals per match")
    ax.tick_params(axis="x", rotation=25)
    ax.spines[["top", "right"]].set_visible(False)
    medians = plot_data.groupby("Season")["Total goals"].median().sort_values(ascending=False)
    _add_insight(fig, f"{medians.index[0]} had the highest median goals per match ({medians.iloc[0]:.1f}).")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "goal_distribution_by_season_boxplot.png")
    return plot_data


def analyze_halftime_fulltime(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.DataFrame:
    """RQ3: count how often each half-time result becomes each full-time result."""
    _require_columns(data, {"HTR", "FTR"}, "Half-time/full-time heatmap")
    table = pd.crosstab(data["HTR"], data["FTR"]).reindex(
        index=RESULT_ORDER, columns=RESULT_ORDER, fill_value=0
    )
    table.index = [RESULT_LABELS[code] for code in table.index]
    table.columns = [RESULT_LABELS[code] for code in table.columns]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    sns.heatmap(table, annot=True, fmt="d", cmap="Blues", linewidths=0.5, cbar_kws={"label": "Matches"}, ax=ax)
    ax.set(title="Half-time result vs full-time result", xlabel="Full-time result", ylabel="Half-time result")
    transition = table.stack().idxmax()
    count = int(table.loc[transition[0], transition[1]])
    _add_insight(fig, f"Most common transition: {transition[0]} → {transition[1]} ({count:,} matches).")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "halftime_fulltime_heatmap.png")
    return table


def analyze_match_statistics(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.DataFrame:
    """RQ5: correlate available match totals (goals, shots, shots on target, corners)."""
    columns = {"FTHG", "FTAG", "HS", "AS", "HST", "AST", "HC", "AC"}
    _require_columns(data, columns, "Match-statistics correlation heatmap")
    totals = pd.DataFrame(
        {
            "Total goals": _combined_stat(data, "FTHG", "FTAG"),
            "Total shots": _combined_stat(data, "HS", "AS"),
            "Shots on target": _combined_stat(data, "HST", "AST"),
            "Corners": _combined_stat(data, "HC", "AC"),
        }
    )
    correlation = totals.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0,
                square=True, linewidths=0.5, cbar_kws={"label": "Pearson correlation"}, ax=ax)
    ax.set(title="Correlation between match statistics")
    pairs = [
        (float(correlation.loc[a, b]), a, b)
        for i, a in enumerate(correlation.columns)
        for b in correlation.columns[i + 1 :]
        if pd.notna(correlation.loc[a, b])
    ]
    if pairs:
        value, stat_a, stat_b = max(pairs, key=lambda pair: abs(pair[0]))
        insight = f"Strongest pair: {stat_a} and {stat_b} (Pearson r = {value:.2f})."
    else:
        insight = "Not enough variation to calculate a pairwise correlation."
    _add_insight(fig, insight)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "match_statistics_correlation_heatmap.png")
    return correlation


def analyze_goals_vs_shots(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.DataFrame:
    """RQ5: show the relationship between total shots and total goals."""
    _require_columns(data, {"FTHG", "FTAG", "HS", "AS"}, "Goals-versus-shots scatter plot")
    plot_data = pd.DataFrame(
        {
            "Total shots": _combined_stat(data, "HS", "AS"),
            "Total goals": _combined_stat(data, "FTHG", "FTAG"),
        }
    )
    if "Season" in data.columns:
        plot_data["Season"] = data["Season"].astype(str).to_numpy()
    plot_data = plot_data.dropna(subset=["Total shots", "Total goals"])

    fig, ax = plt.subplots(figsize=(8, 5.5))
    if plot_data.empty:
        ax.text(
            0.5,
            0.5,
            "No complete shot data is available\nfor this set of match files.",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="#475467",
        )
        ax.set(title="More shots and more goals?", xlabel="Total shots (home + away)", ylabel="Total goals (home + away)")
        shot_goal_corr = float("nan")
        insight = "Scatter plot unavailable because the CSV files contain no complete shot totals."
    elif "Season" in plot_data:
        sns.scatterplot(data=plot_data, x="Total shots", y="Total goals", hue="Season", alpha=0.65,
                        palette=SEASON_PALETTE, ax=ax)
        ax.legend(title="Season", bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.set(title="More shots and more goals?", xlabel="Total shots (home + away)", ylabel="Total goals (home + away)")
        ax.spines[["top", "right"]].set_visible(False)
        shot_goal_corr = plot_data["Total shots"].corr(plot_data["Total goals"])
        insight = (
            f"Total shots and goals had Pearson r = {shot_goal_corr:.2f}."
            if pd.notna(shot_goal_corr)
            else "Not enough variation to estimate the shots-goals correlation."
        )
    else:
        sns.scatterplot(data=plot_data, x="Total shots", y="Total goals", color="#3973ac", alpha=0.65, ax=ax)
        ax.set(title="More shots and more goals?", xlabel="Total shots (home + away)", ylabel="Total goals (home + away)")
        ax.spines[["top", "right"]].set_visible(False)
        shot_goal_corr = plot_data["Total shots"].corr(plot_data["Total goals"])
        insight = (
            f"Total shots and goals had Pearson r = {shot_goal_corr:.2f}."
            if pd.notna(shot_goal_corr)
            else "Not enough variation to estimate the shots-goals correlation."
        )
    _add_insight(fig, insight)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "goals_vs_shots_scatter.png")
    return plot_data


def analyze_season_comparison(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> pd.DataFrame:
    """Compare completed-match count, mean goals, and home-win rate by season."""
    _require_columns(data, {"Season", "FTHG", "FTAG", "FTR"}, "Season comparison chart")
    summary = pd.DataFrame({"Season": data["Season"].astype(str), "Total goals": _combined_stat(data, "FTHG", "FTAG"),
                            "FTR": data["FTR"].astype("string")}).dropna()
    summary = summary.groupby("Season", sort=True).agg(
        Matches=("Total goals", "size"), MeanGoals=("Total goals", "mean"), HomeWinRate=("FTR", lambda x: x.eq("H").mean() * 100)
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(summary["Season"], summary["MeanGoals"], color=sns.color_palette(SEASON_PALETTE, len(summary)))
    ax.bar_label(bars, labels=[f"{value:.2f}" for value in summary["MeanGoals"]], padding=3)
    ax.set(title="Average goals per match by season", xlabel="Season", ylabel="Mean total goals")
    ax.tick_params(axis="x", rotation=20)
    ax.spines[["top", "right"]].set_visible(False)
    top_season = summary.sort_values("MeanGoals", ascending=False).iloc[0]
    _add_insight(fig, f"{top_season['Season']} had the highest mean: {top_season['MeanGoals']:.2f} goals per match.")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    _save(fig, output_dir, "season_average_goals.png")
    return summary


def generate_all_visualizations(
    data: pd.DataFrame, output_dir: str | Path = "charts"
) -> dict[str, object]:
    """Create all T13 charts and return the summary tables used to make them."""
    return {
        "home_advantage": analyze_home_advantage(data, output_dir),
        "team_performance": analyze_team_performance(data, output_dir),
        "goal_distribution": analyze_goal_distribution(data, output_dir),
        "goal_boxplot_data": analyze_goal_boxplot(data, output_dir),
        "halftime_fulltime": analyze_halftime_fulltime(data, output_dir),
        "match_statistics_correlation": analyze_match_statistics(data, output_dir),
        "goals_vs_shots": analyze_goals_vs_shots(data, output_dir),
        "season_comparison": analyze_season_comparison(data, output_dir),
    }
