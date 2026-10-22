from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analytics import (
    build_analytics,
    export_analytics,
    filter_records,
    head_to_head,
    prepare_matches,
    team_match_records,
)


def sample() -> pd.DataFrame:
    return pd.DataFrame({
        "Season": ["2023/24"] * 6,
        "Date": pd.date_range("2023-08-01", periods=6),
        "HomeTeam": ["A", "B", "A", "C", "B", "C"],
        "AwayTeam": ["B", "C", "C", "A", "A", "B"],
        "FTHG": [2, 0, 1, 3, 0, 1], "FTAG": [0, 1, 1, 0, 2, 2],
        "HTHG": [1, 0, 0, 1, 0, 0], "HTAG": [0, 0, 1, 0, 1, 1],
        "HS": [10, 4, 8, 12, 6, 5], "AS": [5, 8, 9, 3, 11, 10],
        "HST": [4, 2, 3, 6, 1, 2], "AST": [1, 3, 3, 1, 4, 5],
        "HC": [4, 2, 5, 7, 3, 2], "AC": [1, 5, 4, 2, 6, 4],
    })


def test_team_records_are_exactly_two_per_fixture_and_points_are_correct():
    matches = prepare_matches(sample())
    records = team_match_records(matches)
    assert len(records) == 2 * len(matches)
    assert records.groupby("MatchID").size().eq(2).all()
    assert records.groupby("MatchID")["Points"].sum().tolist() == [3, 3, 2, 3, 3, 3]


def test_missing_optional_statistics_remain_missing_and_rates_have_nan_denominator():
    data = sample().drop(columns=["HS", "AS", "HST", "AST", "HC", "AC"])
    bundle = build_analytics(data)
    attack = bundle["attacking_summary"]
    assert attack["TotalShots"].isna().all()
    assert attack["ShotAccuracyPct"].isna().all()


def test_filtering_and_head_to_head_are_team_perspective_operations():
    records = team_match_records(prepare_matches(sample()))
    filtered = filter_records(records, team="A", venue="Home")
    assert set(filtered["Team"]) == {"A"}
    assert set(filtered["Venue"]) == {"Home"}
    h2h = head_to_head(records, "A", "B")
    assert len(h2h) == 1 and h2h.iloc[0]["Matches"] == 2


def test_losing_pattern_uses_shot_advantage_for_the_losing_team():
    data = sample()
    data.loc[0, ["FTHG", "FTAG", "HS", "AS", "HST", "AST"]] = [0, 1, 20, 3, 10, 1]
    bundle = build_analytics(data)
    losses = bundle["losing_patterns"]
    row = losses[(losses["Team"] == "A") & (losses["Season"] == "2023/24")].iloc[0]
    assert row["DespiteShotAdvantage"] == 1
    assert row["DespiteShotAdvantageRatePct"] == 50
    assert "DespiteShotDisadvantage" not in losses.columns


def test_export_csv_json_have_matching_row_counts(tmp_path: Path):
    bundle = build_analytics(sample())
    paths = export_analytics(bundle, tmp_path)
    assert len(paths) == 2 * sum(isinstance(value, pd.DataFrame) for value in bundle.values())
    for csv_path in tmp_path.glob("*.csv"):
        json_path = csv_path.with_suffix(".json")
        assert json_path.exists()
        assert len(pd.read_csv(csv_path)) == len(json.loads(json_path.read_text(encoding="utf-8")))
