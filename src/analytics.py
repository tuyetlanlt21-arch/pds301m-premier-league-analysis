"""Reusable Premier League analytics and website-ready exports.

All functions operate on completed fixture rows.  Optional match statistics are
kept as missing values and every rate uses the rows for which its numerator is
observable as its denominator.  The central ``team_match_records`` table gives
each fixture exactly two team-perspective records, preventing double counting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .data_pipeline import clean_matches

TEAM_METRIC_COLUMNS = [
    "GoalsFor", "GoalsAgainst", "ShotsFor", "ShotsAgainst", "ShotsOnTargetFor",
    "ShotsOnTargetAgainst", "CornersFor", "CornersAgainst", "HTGoalsFor",
    "HTGoalsAgainst",
]


def _rate(numerator: float | int, denominator: float | int) -> float:
    return float(numerator / denominator * 100) if denominator else np.nan


def _ratio(numerator: float | int, denominator: float | int) -> float:
    return float(numerator / denominator) if denominator else np.nan


def _mean(series: pd.Series) -> float:
    return float(series.mean()) if series.notna().any() else np.nan


def _numeric(data: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(data[column], errors="coerce") if column in data else pd.Series(np.nan, index=data.index)


def prepare_matches(data: pd.DataFrame, normalize: bool = True) -> pd.DataFrame:
    """Clean, normalize, feature-engineer and chronologically sort fixtures."""
    matches, _ = clean_matches(data)
    if normalize:
        mapping = {
            "Brighton": "Brighton & Hove Albion", "Man City": "Manchester City",
            "Man United": "Manchester United", "Newcastle": "Newcastle United",
            "Nott'm Forest": "Nottingham Forest", "Tottenham": "Tottenham Hotspur",
            "West Ham": "West Ham United", "Wolves": "Wolverhampton Wanderers",
        }
        for side in ("HomeTeam", "AwayTeam"):
            matches[side] = matches[side].replace(mapping)
    matches = matches.sort_values(["Date", "Season", "HomeTeam", "AwayTeam"]).reset_index(drop=True)
    matches.insert(0, "MatchID", np.arange(1, len(matches) + 1))
    matches["total_goals"] = matches["FTHG"] + matches["FTAG"]
    matches["goal_difference"] = matches["FTHG"] - matches["FTAG"]
    matches["total_shots"] = _numeric(matches, "HS") + _numeric(matches, "AS")
    matches["total_shots_on_target"] = _numeric(matches, "HST") + _numeric(matches, "AST")
    matches["total_corners"] = _numeric(matches, "HC") + _numeric(matches, "AC")
    matches["high_scoring"] = matches["total_goals"] >= 4
    return matches


def _perspective(row: pd.Series, home: bool) -> dict[str, object]:
    side = "Home" if home else "Away"
    other = "Away" if home else "Home"
    result = row["FTR"] if home else {"H": "A", "A": "H", "D": "D"}[row["FTR"]]
    ht_result = row.get("HTR", pd.NA)
    if pd.notna(ht_result) and not home:
        ht_result = {"H": "A", "A": "H", "D": "D"}[ht_result]
    record: dict[str, object] = {
        "MatchID": row["MatchID"], "Season": row["Season"], "Date": row["Date"],
        "Team": row[f"{side}Team"], "Opponent": row[f"{other}Team"], "Venue": "Home" if home else "Away",
        "GoalsFor": row[f"FT{side[0]}G"], "GoalsAgainst": row[f"FT{other[0]}G"],
        "Result": result, "Points": {"H": 3, "D": 1, "A": 0}[result],
        "HTGoalsFor": row.get(f"HT{side[0]}G", np.nan), "HTGoalsAgainst": row.get(f"HT{other[0]}G", np.nan),
        "HTResult": ht_result,
        "ShotsFor": row.get("HS" if home else "AS", np.nan), "ShotsAgainst": row.get("AS" if home else "HS", np.nan),
        "ShotsOnTargetFor": row.get("HST" if home else "AST", np.nan), "ShotsOnTargetAgainst": row.get("AST" if home else "HST", np.nan),
        "CornersFor": row.get("HC" if home else "AC", np.nan), "CornersAgainst": row.get("AC" if home else "HC", np.nan),
    }
    record["GoalDifference"] = record["GoalsFor"] - record["GoalsAgainst"]
    record["ShotDifference"] = record["ShotsFor"] - record["ShotsAgainst"] if pd.notna(record["ShotsFor"]) and pd.notna(record["ShotsAgainst"]) else np.nan
    record["SOTDifference"] = record["ShotsOnTargetFor"] - record["ShotsOnTargetAgainst"] if pd.notna(record["ShotsOnTargetFor"]) and pd.notna(record["ShotsOnTargetAgainst"]) else np.nan
    record["LeadingAtHT"] = record["HTResult"] == "H"
    record["TrailingAtHT"] = record["HTResult"] == "A"
    record["DrawingAtHT"] = record["HTResult"] == "D"
    record["CleanSheet"] = record["GoalsAgainst"] == 0
    record["Scored"] = record["GoalsFor"] > 0
    return record


def team_match_records(matches: pd.DataFrame) -> pd.DataFrame:
    """Derive exactly two rows per completed fixture, one for each team."""
    required = {"MatchID", "Season", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    missing = sorted(required - set(matches.columns))
    if missing:
        raise ValueError(f"team_match_records requires columns: {', '.join(missing)}")
    rows = [record for _, match in matches.iterrows() for record in (_perspective(match, True), _perspective(match, False))]
    return pd.DataFrame(rows).sort_values(["Date", "MatchID", "Venue"]).reset_index(drop=True)


def _streak(values: Iterable[bool], longest: bool = True) -> int:
    current = best = 0
    for value in values:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def _team_streaks(group: pd.DataFrame) -> dict[str, int]:
    ordered = group.sort_values(["Date", "MatchID"])
    return {
        "LongestWinningStreak": _streak(ordered["Result"].eq("H")),
        "LongestLosingStreak": _streak(ordered["Result"].eq("A")),
        "LongestUnbeatenStreak": _streak(~ordered["Result"].eq("A")),
        "LongestWinlessStreak": _streak(~ordered["Result"].eq("H")),
    }


def _aggregate(group: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, frame in group.groupby(keys, dropna=False, sort=True):
        if not isinstance(key, tuple): key = (key,)
        row = dict(zip(keys, key))
        n = len(frame)
        wins, draws, losses = frame["Result"].eq("H").sum(), frame["Result"].eq("D").sum(), frame["Result"].eq("A").sum()
        row.update({"Matches": n, "Wins": int(wins), "Draws": int(draws), "Losses": int(losses),
                    "WinRatePct": _rate(wins, n), "DrawRatePct": _rate(draws, n), "LossRatePct": _rate(losses, n),
                    "Points": int(frame["Points"].sum()), "PointsPerMatch": _ratio(frame["Points"].sum(), n),
                    "GoalsScored": int(frame["GoalsFor"].sum()), "GoalsConceded": int(frame["GoalsAgainst"].sum()),
                    "GoalsScoredPerMatch": _ratio(frame["GoalsFor"].sum(), n), "GoalsConcededPerMatch": _ratio(frame["GoalsAgainst"].sum(), n),
                    "GoalDifference": int(frame["GoalDifference"].sum()), "CleanSheets": int(frame["CleanSheet"].sum()),
                    "CleanSheetRatePct": _rate(frame["CleanSheet"].sum(), n), "FailedToScoreRatePct": _rate((~frame["Scored"]).sum(), n),
                    "Conceded1PlusRatePct": _rate((frame["GoalsAgainst"] >= 1).sum(), n),
                    "Conceded2PlusRatePct": _rate((frame["GoalsAgainst"] >= 2).sum(), n),
                    "Conceded3PlusRatePct": _rate((frame["GoalsAgainst"] >= 3).sum(), n),
                    "Conceded0Count": int((frame["GoalsAgainst"] == 0).sum()), "Conceded1Count": int((frame["GoalsAgainst"] == 1).sum()),
                    "Conceded2Count": int((frame["GoalsAgainst"] == 2).sum()), "Conceded3Count": int((frame["GoalsAgainst"] == 3).sum()),
                    "Conceded4PlusCount": int((frame["GoalsAgainst"] >= 4).sum()),
                    "TotalShots": frame["ShotsFor"].sum(min_count=1), "TotalShotsOnTarget": frame["ShotsOnTargetFor"].sum(min_count=1),
                    "ShotsPerMatch": _mean(frame["ShotsFor"]), "ShotsOnTargetPerMatch": _mean(frame["ShotsOnTargetFor"]),
                    "ShotAccuracyPct": _rate(frame["ShotsOnTargetFor"].sum(min_count=1), frame["ShotsFor"].sum(min_count=1)) if frame["ShotsFor"].notna().any() else np.nan,
                    "ShotConversionPct": _rate(frame["GoalsFor"].sum(), frame["ShotsFor"].sum(min_count=1)) if frame["ShotsFor"].notna().any() else np.nan,
                    "GoalsPerShotOnTarget": _ratio(frame["GoalsFor"].sum(), frame["ShotsOnTargetFor"].sum(min_count=1)) if frame["ShotsOnTargetFor"].notna().any() else np.nan,
                    "GoalDifferenceStdDev": frame["GoalDifference"].std(ddof=1) if n > 1 else 0.0,
                    "PerformanceVolatility": frame["Points"].std(ddof=1) if n > 1 else 0.0})
        rows.append(row)
    return pd.DataFrame(rows)


def team_season_summary(records: pd.DataFrame) -> pd.DataFrame:
    """Return the principal team-season score, defence, attack and form metrics."""
    result = _aggregate(records, ["Season", "Team"])
    streaks = records.groupby(["Season", "Team"], group_keys=False).apply(_team_streaks, include_groups=False).apply(pd.Series).reset_index()
    return result.merge(streaks, on=["Season", "Team"], how="left")


def home_away_summary(records: pd.DataFrame) -> pd.DataFrame:
    """Return team-by-venue performance and home advantage versus away points."""
    result = _aggregate(records, ["Season", "Team", "Venue"])
    pivot = result.pivot_table(index=["Season", "Team"], columns="Venue", values="PointsPerMatch", aggfunc="first")
    pivot.columns = [f"{c}PointsPerMatch" for c in pivot.columns]
    pivot = pivot.reset_index()
    if "HomePointsPerMatch" not in pivot: pivot["HomePointsPerMatch"] = np.nan
    if "AwayPointsPerMatch" not in pivot: pivot["AwayPointsPerMatch"] = np.nan
    pivot["HomeAdvantageGap"] = pivot["HomePointsPerMatch"] - pivot["AwayPointsPerMatch"]
    return result.merge(pivot, on=["Season", "Team"], how="left")


def attacking_summary(records: pd.DataFrame) -> pd.DataFrame:
    return team_season_summary(records)[["Season", "Team", "GoalsScored", "GoalsScoredPerMatch", "TotalShots", "TotalShotsOnTarget", "ShotsPerMatch", "ShotsOnTargetPerMatch", "ShotAccuracyPct", "ShotConversionPct", "GoalsPerShotOnTarget"]]


def defensive_summary(records: pd.DataFrame) -> pd.DataFrame:
    cols = ["Season", "Team", "GoalsConceded", "GoalsConcededPerMatch", "Conceded1PlusRatePct", "Conceded2PlusRatePct", "Conceded3PlusRatePct", "CleanSheets", "CleanSheetRatePct", "Conceded0Count", "Conceded1Count", "Conceded2Count", "Conceded3Count", "Conceded4PlusCount", "GoalDifferenceStdDev"]
    return team_season_summary(records)[cols]


def _pattern_summary(records: pd.DataFrame, wins: bool) -> pd.DataFrame:
    frame = records[records["Result"].eq("H" if wins else "A")].copy()
    if frame.empty: return pd.DataFrame(columns=["Season", "Team"])
    frame["Margin"] = frame["GoalDifference"].abs()
    frame["Margin1"] = frame["Margin"].eq(1); frame["Margin2"] = frame["Margin"].eq(2); frame["Margin3Plus"] = frame["Margin"].ge(3)
    frame["WithoutConceding"] = frame["GoalsAgainst"].eq(0)
    frame["AfterTrailingAtHT"] = frame["TrailingAtHT"]
    frame["AfterDrawingAtHT"] = frame["DrawingAtHT"]
    if wins:
        frame["DespiteShotDisadvantage"] = frame["ShotDifference"].lt(0)
        frame["DespiteSOTDisadvantage"] = frame["SOTDifference"].lt(0)
    else:
        frame["DespiteScoring"] = frame["Scored"]
        frame["DespiteShotAdvantage"] = frame["ShotDifference"].gt(0)
        frame["DespiteSOTAdvantage"] = frame["SOTDifference"].gt(0)
        frame["AfterLeadingAtHT"] = frame["LeadingAtHT"]
    group = frame.groupby(["Season", "Team"])
    result = group.size().rename("Wins" if wins else "Losses").to_frame()
    for col in frame.columns:
        if col in {"Margin1", "Margin2", "Margin3Plus", "WithoutConceding", "DespiteShotDisadvantage", "DespiteSOTDisadvantage", "AfterTrailingAtHT", "AfterDrawingAtHT", "DespiteScoring", "DespiteShotAdvantage", "DespiteSOTAdvantage", "AfterLeadingAtHT"}:
            result[col] = group[col].sum(min_count=1)
    result["AverageMargin"] = group["Margin"].mean()
    result = result.reset_index()
    total_column = "Wins" if wins else "Losses"
    rate_columns = [c for c in result.columns if c not in {"Season", "Team", total_column, "AverageMargin"}]
    for column in rate_columns:
        result[f"{column}RatePct"] = result[column] / result[total_column] * 100
    return result


def losing_patterns(records: pd.DataFrame) -> pd.DataFrame:
    return _pattern_summary(records, False)


def winning_patterns(records: pd.DataFrame) -> pd.DataFrame:
    return _pattern_summary(records, True)


def half_time_full_time_summary(matches: pd.DataFrame, records: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Return transition counts plus comeback, lost-lead and preservation rates."""
    valid = matches.dropna(subset=["HTR", "FTR"])
    matrix = pd.crosstab(valid["HTR"], valid["FTR"]).reindex(index=["H", "D", "A"], columns=["H", "D", "A"], fill_value=0)
    if records is None: records = team_match_records(matches)
    r = records.dropna(subset=["HTResult"])
    lead = r[r["HTResult"].eq("H")]
    deficit = r[r["HTResult"].eq("A")]
    team = r.groupby(["Season", "Team"])
    dynamics = team.apply(lambda g: pd.Series({
        "HalfTimeLeads": int(g["LeadingAtHT"].sum()), "PreservedHalfTimeLeads": int((g["LeadingAtHT"] & g["Result"].eq("H")).sum()),
        "LeadPreservationRatePct": _rate((g["LeadingAtHT"] & g["Result"].eq("H")).sum(), g["LeadingAtHT"].sum()),
        "ComebackWins": int((g["TrailingAtHT"] & g["Result"].eq("H")).sum()), "ComebackDraws": int((g["TrailingAtHT"] & g["Result"].eq("D")).sum()),
        "ComebackSuccessRatePct": _rate((g["TrailingAtHT"] & g["Result"].eq("H")).sum(), g["TrailingAtHT"].sum()),
        "LostLeads": int((g["LeadingAtHT"] & ~g["Result"].eq("H")).sum()), "LostLeadRatePct": _rate((g["LeadingAtHT"] & ~g["Result"].eq("H")).sum(), g["LeadingAtHT"].sum()),
    }), include_groups=False).reset_index()
    return {"transition_matrix": matrix.reset_index(names="HTR"), "team_dynamics": dynamics, "overall": pd.DataFrame({"Metric": ["Comeback wins", "Comeback draws", "Lost leads"], "Count": [int((deficit["Result"] == "H").sum()), int((deficit["Result"] == "D").sum()), int((lead["Result"] != "H").sum())]})}


def goal_distribution(matches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    goals = matches["total_goals"] if "total_goals" in matches else matches["FTHG"] + matches["FTAG"]
    counts = goals.value_counts().reindex([0, 1, 2, 3], fill_value=0).rename("Matches").to_frame()
    counts.loc["4+"] = int((goals >= 4).sum())
    stats = pd.DataFrame({"Metric": ["Mean", "Median", "Mode", "StandardDeviation", "HighScoringRatePct"], "Value": [goals.mean(), goals.median(), goals.mode().iloc[0], goals.std(ddof=1) if len(goals) > 1 else 0.0, _rate((goals >= 4).sum(), len(goals))]})
    seasonal = matches.assign(total_goals=goals).groupby("Season").agg(Matches=("total_goals", "size"), GoalsPerMatch=("total_goals", "mean"), MedianGoals=("total_goals", "median"), GoalStdDev=("total_goals", "std")).reset_index()
    return {"distribution": counts.reset_index(names="GoalBucket"), "statistics": stats, "seasonal": seasonal}


def form_and_consistency(records: pd.DataFrame, last_n: int = 5) -> pd.DataFrame:
    rows = []
    for (season, team), group in records.groupby(["Season", "Team"]):
        ordered = group.sort_values(["Date", "MatchID"])
        recent = ordered.tail(last_n)
        rows.append({"Season": season, "Team": team, "LastFiveResults": "".join(recent["Result"].tolist()), "LastFivePoints": int(recent["Points"].sum()), "RollingPointsPerMatch": _ratio(recent["Points"].sum(), len(recent)), "RollingGoalsScored": _mean(recent["GoalsFor"]), "RollingGoalsConceded": _mean(recent["GoalsAgainst"]), "LastFiveMatches": len(recent), "GoalDifferenceStdDev": ordered["GoalDifference"].std(ddof=1) if len(ordered) > 1 else 0.0, **_team_streaks(ordered)})
    return pd.DataFrame(rows)


def season_summary(matches: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, frame in matches.groupby("Season"):
        r = records[records["Season"].eq(season)]
        teams = set(frame["HomeTeam"]) | set(frame["AwayTeam"]); n = len(frame)
        expected = len(teams) * (len(teams) - 1)
        rows.append({"Season": season, "CompletedMatches": n, "ParticipatingTeams": len(teams), "ExpectedMatchesForParticipatingTeams": expected, "IsCompleteSeason": bool(n >= 380 if len(teams) >= 20 else n >= expected), "GoalsPerMatch": frame["total_goals"].mean(), "HomeWinRatePct": _rate((frame["FTR"] == "H").sum(), n), "DrawRatePct": _rate((frame["FTR"] == "D").sum(), n), "AwayWinRatePct": _rate((frame["FTR"] == "A").sum(), n), "HomeGoalsPerMatch": frame["FTHG"].mean(), "AwayGoalsPerMatch": frame["FTAG"].mean(), "TeamRecords": len(r)})
    return pd.DataFrame(rows)


def head_to_head(records: pd.DataFrame, team_a: str | None = None, team_b: str | None = None) -> pd.DataFrame:
    frame = records.copy()
    if team_a and team_b:
        frame = frame[frame["Team"].eq(team_a) & frame["Opponent"].eq(team_b)]
    return _aggregate(frame, ["Season", "Team", "Opponent"]) if not frame.empty else pd.DataFrame()


def compare_teams(records: pd.DataFrame, team_a: str, team_b: str, season: str | None = None) -> dict[str, pd.DataFrame]:
    frame = records[records["Team"].isin([team_a, team_b])]
    if season is not None: frame = frame[frame["Season"].eq(season)]
    overall = _aggregate(frame, ["Team"])
    venue = _aggregate(frame, ["Team", "Venue"])
    form = form_and_consistency(frame)
    h2h = head_to_head(records, team_a, team_b)
    return {"overall": overall, "home_away": venue, "form": form, "head_to_head": h2h}


def match_efficiency(matches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return shot/corner outcome comparisons and Pearson associations."""
    frame = matches.copy()
    frame["TotalShots"] = _numeric(frame, "HS") + _numeric(frame, "AS")
    frame["TotalShotsOnTarget"] = _numeric(frame, "HST") + _numeric(frame, "AST")
    frame["TotalCorners"] = _numeric(frame, "HC") + _numeric(frame, "AC")
    totals = frame[["total_goals", "TotalShots", "TotalShotsOnTarget", "TotalCorners"]].rename(columns={"total_goals": "TotalGoals"})
    correlations = totals.corr(numeric_only=True)
    outcome = totals.assign(FTR=frame["FTR"]).groupby("FTR")[list(totals.columns)].mean().reset_index()
    records = team_match_records(frame)
    by_result = records.groupby("Result")
    pattern = by_result.size().rename("Matches").to_frame()
    for name, flag in {
        "ShotDominance": records["ShotDifference"] > 0,
        "SOTDominance": records["SOTDifference"] > 0,
        "WinsDespiteShotDisadvantage": records["Result"].eq("H") & records["ShotDifference"].lt(0),
        "LossesDespiteShotAdvantage": records["Result"].eq("A") & records["ShotDifference"].gt(0),
        "WinsDespiteSOTDisadvantage": records["Result"].eq("H") & records["SOTDifference"].lt(0),
        "LossesDespiteSOTAdvantage": records["Result"].eq("A") & records["SOTDifference"].gt(0),
    }.items():
        pattern[name] = flag.groupby(records["Result"]).sum()
    pattern = pattern.reset_index()
    return {"correlations": correlations, "outcome_comparison": outcome, "outcome_efficiency_patterns": pattern}


def filter_records(records: pd.DataFrame, season: str | None = None, team: str | None = None, opponent: str | None = None, venue: str | None = None, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """Filter team-match records without changing their order or values."""
    result = records.copy()
    if season is not None: result = result[result["Season"].eq(season)]
    if team is not None: result = result[result["Team"].eq(team)]
    if opponent is not None: result = result[result["Opponent"].eq(opponent)]
    if venue is not None: result = result[result["Venue"].eq(venue)]
    if start_date is not None: result = result[result["Date"] >= pd.Timestamp(start_date)]
    if end_date is not None: result = result[result["Date"] <= pd.Timestamp(end_date)]
    return result.reset_index(drop=True)


def build_analytics(data: pd.DataFrame) -> dict[str, object]:
    """Build every dashboard-facing table from a raw or cleaned match frame."""
    matches = prepare_matches(data)
    records = team_match_records(matches)
    dynamics = half_time_full_time_summary(matches, records)
    goals = goal_distribution(matches)
    efficiency = match_efficiency(matches)
    return {"cleaned_matches": matches, "team_match": records, "team_season_summary": team_season_summary(records), "team_home_away_summary": home_away_summary(records), "defensive_summary": defensive_summary(records), "attacking_summary": attacking_summary(records), "losing_patterns": losing_patterns(records), "winning_patterns": winning_patterns(records), "form_consistency_summary": form_and_consistency(records), "half_time_full_time_summary": dynamics["team_dynamics"], "half_time_full_time_transition": dynamics["transition_matrix"], "goal_distribution": goals["distribution"], "goal_statistics": goals["statistics"], "season_summary": season_summary(matches, records), "efficiency_correlations": efficiency["correlations"].reset_index(names="Metric"), "efficiency_outcome_comparison": efficiency["outcome_comparison"], "efficiency_patterns": efficiency["outcome_efficiency_patterns"]}


def export_analytics(bundle: dict[str, object], output_dir: str | Path) -> list[Path]:
    """Write each dashboard table as CSV and JSON; return written paths."""
    destination = Path(output_dir); destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, value in bundle.items():
        if not isinstance(value, pd.DataFrame): continue
        csv_path = destination / f"{name}.csv"; json_path = destination / f"{name}.json"
        value.to_csv(csv_path, index=False)
        json_path.write_text(json.dumps(value.replace({np.nan: None}).to_dict(orient="records"), default=str, ensure_ascii=False, indent=2), encoding="utf-8")
        paths.extend([csv_path, json_path])
    return paths
