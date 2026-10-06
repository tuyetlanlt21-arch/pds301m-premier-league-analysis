"""Reusable CSV loading, cleaning, feature engineering, and audit helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
OPTIONAL_NUMERIC_COLUMNS = ["HTHG", "HTAG", "HS", "AS", "HST", "AST", "HC", "AC"]
RESULTS = ("H", "D", "A")


def total_goals(home_goals: int | float, away_goals: int | float) -> int | float:
    """Return the combined full-time goals for a match."""
    return home_goals + away_goals


def result_label(code: str) -> str:
    """Map a Football-Data result code to a readable label."""
    labels = {"H": "Home win", "D": "Draw", "A": "Away win"}
    try:
        return labels[code]
    except KeyError as exc:
        raise ValueError(f"Unknown result code: {code!r}") from exc


def points_for_result(code: str) -> tuple[int, int]:
    """Return (home points, away points) under the 3-1-0 league rule."""
    points = {"H": (3, 0), "D": (1, 1), "A": (0, 3)}
    try:
        return points[code]
    except KeyError as exc:
        raise ValueError(f"Unknown result code: {code!r}") from exc


def classify_match(goals: int | float) -> str:
    """Classify a match as high-scoring when it has at least four goals."""
    return "High scoring (4+)" if goals >= 4 else "Under 4 goals"


def unique_teams(records: list[dict[str, Any]]) -> set[str]:
    """Collect unique home and away team names from dictionary records."""
    return {
        str(record[key]).strip()
        for record in records
        for key in ("HomeTeam", "AwayTeam")
        if pd.notna(record.get(key)) and str(record[key]).strip()
    }


def team_appearances(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count team appearances from dictionary match records."""
    counts: dict[str, int] = {}
    for record in records:
        for side in ("HomeTeam", "AwayTeam"):
            team = record.get(side)
            if pd.notna(team) and str(team).strip():
                name = str(team).strip()
                counts[name] = counts.get(name, 0) + 1
    return counts


def match_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    """Build a stable match identifier from season, date, and both teams."""
    return tuple(
        str(record.get(column, "")).strip()
        for column in ("Season", "Date", "HomeTeam", "AwayTeam")
    )  # type: ignore[return-value]


def _season_from_path(path: Path) -> str | None:
    match = re.search(r"(?<!\d)(\d{2})(\d{2})(?!\d)", path.stem)
    if not match:
        return None
    start, end = map(int, match.groups())
    century_start = 2000 + start if start < 70 else 1900 + start
    century_end = 2000 + end if end < 70 else 1900 + end
    return f"{century_start}/{str(century_end)[-2:]}"


def load_raw_csvs(raw_dir: str | Path) -> tuple[pd.DataFrame, list[Path]]:
    """Read saved season CSVs, attach season labels, and return rows and paths.

    The function is deliberately offline: it reads only CSV files already saved
    under ``raw_dir``. Files can be named ``epl_2324_raw.csv`` or similar.
    """
    directory = Path(raw_dir)
    paths = sorted(directory.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"No season CSV files found in {directory}")

    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
        frame.columns = [str(column).strip().lstrip("\ufeff") for column in frame.columns]
        if "Season" not in frame.columns:
            season = _season_from_path(path)
            if season is None:
                raise ValueError(
                    f"Cannot infer season from {path.name}; add a Season column "
                    "or use a filename containing a season code such as 2324."
                )
            frame["Season"] = season
        frame["SourceFile"] = path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False), paths


def inspect_data(data: pd.DataFrame) -> dict[str, Any]:
    """Return counts that help document raw-data quality before cleaning."""
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    normalized = data.copy()
    for column in ("HomeTeam", "AwayTeam"):
        normalized[column] = normalized[column].astype("string").str.strip()
    score_missing = data[["FTHG", "FTAG"]].isna().any(axis=1)
    invalid_team = normalized[["HomeTeam", "AwayTeam"]].isna().any(axis=1)
    key_columns = [column for column in ("Season", "Date", "HomeTeam", "AwayTeam") if column in data]
    duplicate_count = int(normalized.duplicated(key_columns).sum()) if key_columns else 0
    return {
        "row_count": len(data),
        "column_count": len(data.columns),
        "missing_by_column": data.isna().sum().sort_values(ascending=False),
        "incomplete_matches": int((score_missing | invalid_team).sum()),
        "duplicate_matches": duplicate_count,
        "rows_by_season": data.groupby("Season", dropna=False).size() if "Season" in data else pd.Series(dtype="int64"),
    }


def clean_matches(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean completed fixtures and calculate a consistent full-time result.

    Missing optional match statistics are preserved as missing values. They are
    excluded pairwise from the affected summaries rather than filled with zero.
    """
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    clean = data.copy()
    clean.columns = [str(column).strip().lstrip("\ufeff") for column in clean.columns]
    for column in ("HomeTeam", "AwayTeam"):
        clean[column] = clean[column].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
        clean[column] = clean[column].replace("", pd.NA)
    clean["Date"] = pd.to_datetime(clean["Date"], dayfirst=True, errors="coerce")
    for column in ["FTHG", "FTAG", *OPTIONAL_NUMERIC_COLUMNS]:
        if column in clean:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
        elif column in OPTIONAL_NUMERIC_COLUMNS:
            # Preserve a consistent schema while clearly marking unavailable
            # optional statistics as missing rather than as zero.
            clean[column] = np.nan

    before = len(clean)
    complete = clean["Date"].notna() & clean["HomeTeam"].notna() & clean["AwayTeam"].notna()
    complete &= clean["FTHG"].notna() & clean["FTAG"].notna()
    complete &= clean["FTHG"].ge(0) & clean["FTAG"].ge(0)
    clean = clean.loc[complete].copy()
    clean["FTR"] = np.select(
        [clean["FTHG"] > clean["FTAG"], clean["FTHG"] == clean["FTAG"]],
        ["H", "D"], default="A"
    )

    if "HTR" not in clean.columns:
        clean["HTR"] = pd.NA
    if {"HTHG", "HTAG"}.issubset(clean.columns):
        ht_ready = clean["HTHG"].notna() & clean["HTAG"].notna()
        clean.loc[ht_ready, "HTR"] = np.select(
            [clean.loc[ht_ready, "HTHG"] > clean.loc[ht_ready, "HTAG"],
             clean.loc[ht_ready, "HTHG"] == clean.loc[ht_ready, "HTAG"]],
            ["H", "D"], default="A"
        )
    else:
        clean["HTR"] = clean["HTR"].where(clean["HTR"].isin(RESULTS))

    key = [column for column in ("Season", "Date", "HomeTeam", "AwayTeam") if column in clean]
    clean = clean.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
    summary = {
        "raw_rows": before,
        "removed_incomplete_or_invalid": before - int(complete.sum()),
        "removed_duplicates": int(complete.sum()) - len(clean),
        "clean_rows": len(clean),
    }
    return clean, summary


def create_features(data: pd.DataFrame) -> pd.DataFrame:
    """Add reusable match-level outcomes and combined match-statistic totals."""
    features = data.copy()
    features["total_goals"] = features["FTHG"] + features["FTAG"]
    features["goal_difference"] = features["FTHG"] - features["FTAG"]
    features["result_label"] = features["FTR"].map({"H": "Home win", "D": "Draw", "A": "Away win"})
    features["high_scoring"] = features["total_goals"].ge(4)
    for total_name, home_name, away_name in (
        ("total_shots", "HS", "AS"),
        ("total_shots_on_target", "HST", "AST"),
        ("total_corners", "HC", "AC"),
    ):
        if home_name in features and away_name in features:
            features[total_name] = features[home_name] + features[away_name]
    return features


def summarize_by_outcome(data: pd.DataFrame) -> pd.DataFrame:
    """Return counts and outcome rates for home, drawn, and away matches."""
    order = ["H", "D", "A"]
    counts = data["FTR"].value_counts().reindex(order, fill_value=0)
    return pd.DataFrame({"Matches": counts, "Share (%)": counts / max(len(data), 1) * 100}, index=order)
