"""Team-centric descriptive analytics for the Premier League dashboard.

All outputs are derived from completed fixtures; no predictive claims are made.
Rates use eligible observations, never missing optional data as zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED = {"Season", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}


def team_match_records(matches: pd.DataFrame) -> pd.DataFrame:
    """Two observations per match, one from each team's perspective."""
    missing = REQUIRED - set(matches.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if matches.empty:
        raise ValueError("No matches supplied")
    data = matches.copy()
    for col in ("FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST", "HC", "AC"):
        if col not in data:
            data[col] = np.nan
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["Season", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    data = data.loc[data["FTHG"].ge(0) & data["FTAG"].ge(0)].copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Date"])
    if data.empty:
        raise ValueError("No completed matches supplied")
    data = data.reset_index(drop=True)
    data["MatchID"] = np.arange(len(data))
    frames = []
    for home in (True, False):
        prefix, other = ("H", "A") if home else ("A", "H")
        result = pd.DataFrame({
            "MatchID": data["MatchID"], "Season": data["Season"].astype(str),
            "Date": data["Date"],
            "Team": data["HomeTeam"] if home else data["AwayTeam"],
            "Opponent": data["AwayTeam"] if home else data["HomeTeam"],
            "Venue": "Home" if home else "Away",
            "GoalsFor": data["FTHG"] if home else data["FTAG"],
            "GoalsAgainst": data["FTAG"] if home else data["FTHG"],
            "HTGoalsFor": data["HTHG"] if home else data["HTAG"],
            "HTGoalsAgainst": data["HTAG"] if home else data["HTHG"],
            "Shots": data[f"{prefix}S"],
            "OpponentShots": data[f"{other}S"],
            "ShotsOnTarget": data[f"{prefix}ST"],
            "OpponentShotsOnTarget": data[f"{other}ST"],
            "Corners": data[f"{prefix}C"],
            "OpponentCorners": data[f"{other}C"],
        })
        frames.append(result)
    records = pd.concat(frames, ignore_index=True)
    records["GoalDifference"] = records["GoalsFor"] - records["GoalsAgainst"]
    records["Result"] = np.select(
        [records["GoalDifference"].gt(0), records["GoalDifference"].eq(0)],
        ["W", "D"], default="L")
    records["Points"] = records["Result"].map({"W": 3, "D": 1, "L": 0})
    records["CleanSheet"] = records["GoalsAgainst"].eq(0)
    records["HeavyDefeat"] = records["GoalsAgainst"].ge(3) & records["Result"].eq("L")
    records["WinMargin"] = records["GoalDifference"].where(records["Result"].eq("W"))
    ht_known = records[["HTGoalsFor", "HTGoalsAgainst"]].notna().all(axis=1)
    records["TrailingAtHalfTime"] = ht_known & records["HTGoalsFor"].lt(records["HTGoalsAgainst"])
    records["LeadingAtHalfTime"] = ht_known & records["HTGoalsFor"].gt(records["HTGoalsAgainst"])
    records["ComebackWin"] = records["TrailingAtHalfTime"] & records["Result"].eq("W")
    records["ComebackDraw"] = records["TrailingAtHalfTime"] & records["Result"].eq("D")
    records["LostLead"] = records["LeadingAtHalfTime"] & records["Result"].ne("W")
    shots_known = records[["Shots", "OpponentShots"]].notna().all(axis=1)
    records["MoreShots"] = shots_known & records["Shots"].gt(records["OpponentShots"])
    records["LossDespiteMoreShots"] = records["MoreShots"] & records["Result"].eq("L")
    records["ShotAccuracy"] = (records["ShotsOnTarget"] / records["Shots"].replace(0, np.nan))
    records["ShotConversion"] = (records["GoalsFor"] / records["Shots"].replace(0, np.nan))
    records["ShotsPerWin"] = records["Shots"].where(records["Result"].eq("W"))
    return records.sort_values(["Season", "Team", "Date", "MatchID"]).reset_index(drop=True)


def _streak(results: pd.Series, target: str) -> int:
    best = current = 0
    for result in results:
        current = current + 1 if result == target else 0
        best = max(best, current)
    return best


def team_summary(records: pd.DataFrame, by_venue: bool = False) -> pd.DataFrame:
    """Team/season metrics; optional venue dimension for home-away comparisons."""
    keys = ["Season", "Team"] + (["Venue"] if by_venue else [])
    rows = []
    for key, group in records.groupby(keys, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        group = group.sort_values(["Date", "MatchID"])
        n = len(group)
        wins = int(group["Result"].eq("W").sum())
        draws = int(group["Result"].eq("D").sum())
        losses = int(group["Result"].eq("L").sum())
        trailing = int(group["TrailingAtHalfTime"].sum())
        leading = int(group["LeadingAtHalfTime"].sum())
        more_shots = int(group["MoreShots"].sum())
        shots_eligible = group["Shots"].notna().sum()
        rows.append({
            **dict(zip(keys, key)), "Matches": n,
            "Wins": wins, "Draws": draws, "Losses": losses,
            "WinRate": wins / n * 100, "LossRate": losses / n * 100,
            "Points": int(group["Points"].sum()), "PointsPerMatch": group["Points"].mean(),
            "GoalsFor": group["GoalsFor"].sum(), "GoalsAgainst": group["GoalsAgainst"].sum(),
            "GoalDifference": group["GoalDifference"].sum(),
            "GoalsForPerMatch": group["GoalsFor"].mean(),
            "GoalsAgainstPerMatch": group["GoalsAgainst"].mean(),
            "CleanSheets": int(group["CleanSheet"].sum()),
            "CleanSheetRate": group["CleanSheet"].mean() * 100,
            "HeavyDefeats": int(group["HeavyDefeat"].sum()),
            "MeanWinningMargin": group["WinMargin"].mean(),
            "GoalDifferenceStd": group["GoalDifference"].std(ddof=0),
            "LongestWinStreak": _streak(group["Result"], "W"),
            "LongestLossStreak": _streak(group["Result"], "L"),
            "Last5Points": int(group.tail(5)["Points"].sum()),
            "ComebackWins": int(group["ComebackWin"].sum()),
            "ComebackDraws": int(group["ComebackDraw"].sum()),
            "ComebackSuccessRate": (group["ComebackWin"].sum() + group["ComebackDraw"].sum()) / trailing * 100 if trailing else np.nan,
            "LostLeads": int(group["LostLead"].sum()),
            "LostLeadRate": group["LostLead"].sum() / leading * 100 if leading else np.nan,
            "LossesDespiteMoreShots": int(group["LossDespiteMoreShots"].sum()),
            "LossDespiteMoreShotsRate": group["LossDespiteMoreShots"].sum() / more_shots * 100 if more_shots else np.nan,
            "Shots": group["Shots"].sum(min_count=1),
            "ShotsOnTarget": group["ShotsOnTarget"].sum(min_count=1),
            "ShotAccuracyRate": group["ShotsOnTarget"].sum(min_count=1) / group["Shots"].sum(min_count=1) * 100 if group["Shots"].sum(min_count=1) > 0 else np.nan,
            "ShotConversionRate": group.loc[group["Shots"].notna(), "GoalsFor"].sum() / group["Shots"].sum(min_count=1) * 100 if group["Shots"].sum(min_count=1) > 0 else np.nan,
            "ShotDataCoverage": shots_eligible / n * 100,
            "MeanShotsInWins": group["ShotsPerWin"].mean(),
        })
    return pd.DataFrame(rows).sort_values(keys).reset_index(drop=True)


def season_summary(records: pd.DataFrame) -> pd.DataFrame:
    """One row per season, useful for overview charts and filter menus."""
    rows = []
    for season, group in records.groupby("Season", sort=True):
        fixtures = group.drop_duplicates("MatchID")
        rows.append({
            "Season": season, "Matches": len(fixtures),
            "Teams": group["Team"].nunique(),
            "GoalsPerMatch": group["GoalsFor"].sum() / len(fixtures),
            "HomeWinRate": group.loc[group["Venue"].eq("Home"), "Result"].eq("W").mean() * 100,
            "DrawRate": group.loc[group["Venue"].eq("Home"), "Result"].eq("D").mean() * 100,
            "AwayWinRate": group.loc[group["Venue"].eq("Away"), "Result"].eq("W").mean() * 100,
        })
    return pd.DataFrame(rows)


def head_to_head(records: pd.DataFrame, team_a: str, team_b: str) -> pd.DataFrame:
    """Only direct fixtures, from team_a's perspective; one row per match."""
    return records.loc[
        records["Team"].eq(team_a) & records["Opponent"].eq(team_b)
    ].sort_values(["Date", "MatchID"]).copy()


def export_dashboard_data(matches: pd.DataFrame, output_dir: str = "data/dashboard") -> dict[str, str]:
    """Export CSV tables and a JSON payload consumable by a static React site."""
    from pathlib import Path
    import json
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records = team_match_records(matches)
    tables = {
        "team_matches": records,
        "team_summary": team_summary(records),
        "team_venue_summary": team_summary(records, by_venue=True),
        "season_summary": season_summary(records),
    }
    paths = {}
    for name, frame in tables.items():
        path = out / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = str(path)
    payload = {name: json.loads(frame.to_json(orient="records", date_format="iso"))
               for name, frame in tables.items()}
    json_path = out / "dashboard.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths["dashboard_json"] = str(json_path)
    return paths
