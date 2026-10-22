"""Focused visualizations for the expanded analytics tables."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _save(fig: plt.Figure, directory: str | Path, filename: str) -> Path:
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def generate_expanded_visualizations(bundle: dict[str, object], output_dir: str | Path) -> list[Path]:
    """Generate four non-redundant dashboard-oriented charts."""
    team = bundle["team_season_summary"]
    venue = bundle["team_home_away_summary"]
    season = bundle["season_summary"]
    assert isinstance(team, pd.DataFrame) and isinstance(venue, pd.DataFrame) and isinstance(season, pd.DataFrame)
    paths: list[Path] = []

    latest = team.groupby("Team", as_index=False).tail(1).sort_values("PointsPerMatch")
    fig, ax = plt.subplots(figsize=(10, max(5, len(latest) * .3)))
    ax.barh(latest["Team"], latest["PointsPerMatch"], color="#1f6f8b")
    ax.set(title="Team points per match", xlabel="Points per match (3–1–0)", ylabel="Team")
    ax.spines[["top", "right"]].set_visible(False)
    paths.append(_save(fig, output_dir, "team_points_per_match.png"))

    latest_venue = venue.groupby("Team", as_index=False).tail(2)
    pivot = latest_venue.pivot_table(index="Team", columns="Venue", values="PointsPerMatch", aggfunc="mean").sort_values("Home")
    fig, ax = plt.subplots(figsize=(10, max(5, len(pivot) * .3)))
    pivot.plot.barh(ax=ax, color=["#d95f02", "#1b9e77"])
    ax.set(title="Home and away points per match", xlabel="Points per match", ylabel="Team")
    ax.legend(title="Venue")
    ax.spines[["top", "right"]].set_visible(False)
    paths.append(_save(fig, output_dir, "home_away_points_per_match.png"))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=season, x="Season", y="GoalsPerMatch", marker="o", ax=ax, color="#7b3294")
    ax.set(title="Goals per match by season", xlabel="Season", ylabel="Goals per completed match")
    ax.tick_params(axis="x", rotation=25); ax.spines[["top", "right"]].set_visible(False)
    paths.append(_save(fig, output_dir, "season_goals_trend.png"))

    latest_for_box = team.groupby("Team", as_index=False).tail(3)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=latest_for_box, x="Season", y="GoalDifferenceStdDev", color="#80cdc1", ax=ax)
    ax.set(title="Team goal-difference volatility", xlabel="Season", ylabel="Standard deviation of goal difference")
    ax.spines[["top", "right"]].set_visible(False)
    paths.append(_save(fig, output_dir, "team_goal_difference_volatility.png"))
    return paths
