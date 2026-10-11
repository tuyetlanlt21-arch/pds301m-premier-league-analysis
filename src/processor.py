"""Validation, cleaning, and team-name normalization for raw match data."""

from pathlib import Path
from typing import Any

import pandas as pd

from .data_pipeline import load_raw_csvs

REQUIRED_COLUMNS: set[str] = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
    "HTHG",
    "HTAG",
    "HTR",
    "HS",
    "AS",
    "HST",
    "AST",
    "HC",
    "AC",
    "Season",
    "Source",
    "CollectionMethod",
    "SourceURL",
    "RetrievedAt",
}
IDENTITY_COLUMNS = ("Season", "Date", "HomeTeam", "AwayTeam")
NUMERIC_COLUMNS = ("FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST", "HC", "AC")
TEAM_NAME_MAPPING = {
    "Brighton": "Brighton & Hove Albion",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
}


class FootballDataProcessor:
    """Define the intended raw-to-processed data lifecycle."""

    def load_csvs(self, raw_dir: Path) -> tuple[pd.DataFrame, list[Path]]:
        """Load all saved season CSVs and attach inferred season metadata."""
        return load_raw_csvs(raw_dir)

    def load_data(self, path: Path) -> pd.DataFrame:
        """Load a collected raw CSV dataset without modifying the source file."""
        return pd.read_csv(path)

    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate schema and required fixture identity without changing data."""
        missing_columns = sorted(REQUIRED_COLUMNS - set(data.columns))
        if missing_columns:
            raise ValueError(f"Data is missing required columns: {', '.join(missing_columns)}")
        for column in IDENTITY_COLUMNS:
            if data[column].isna().any():
                raise ValueError(f"Fixture identity column {column} contains missing values.")
        same_team = data["HomeTeam"].astype(str).str.strip().eq(
            data["AwayTeam"].astype(str).str.strip()
        )
        if same_team.any():
            raise ValueError("HomeTeam and AwayTeam must be different for every fixture.")

        for column in NUMERIC_COLUMNS:
            values = data[column]
            present = values.notna() & values.astype("string").str.strip().ne("")
            numeric_values = pd.to_numeric(values.where(present), errors="coerce")
            invalid = present & numeric_values.isna()
            if invalid.any():
                raise ValueError(f"Numeric column {column} contains a non-numeric value.")
            if numeric_values.lt(0).any():
                raise ValueError(f"Numeric column {column} cannot contain negative values.")
        return data

    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create an analytical copy with completed, consistent, unique fixtures."""
        self.validate_data(data)
        cleaned = data.copy()
        cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce", dayfirst=True)
        for column in NUMERIC_COLUMNS:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

        completed = cleaned[
            cleaned["FTHG"].notna()
            & cleaned["FTAG"].notna()
            & cleaned["FTR"].isin({"H", "D", "A"})
        ].copy()
        expected_results = pd.Series("D", index=completed.index)
        expected_results.loc[completed["FTHG"] > completed["FTAG"]] = "H"
        expected_results.loc[completed["FTHG"] < completed["FTAG"]] = "A"
        if not completed["FTR"].eq(expected_results).all():
            raise ValueError("Completed fixtures have inconsistent FTR values.")
        return completed.drop_duplicates(subset=IDENTITY_COLUMNS, keep="first")

    def normalize_team_names(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with whitespace-trimmed, canonical team names."""
        normalized = data.copy()
        for column in ("HomeTeam", "AwayTeam"):
            normalized[column] = normalized[column].str.strip().replace(TEAM_NAME_MAPPING)
        return normalized

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with the documented match-analysis features."""
        featured = data.copy()
        featured["total_goals"] = featured["FTHG"] + featured["FTAG"]
        featured["goal_difference"] = featured["FTHG"] - featured["FTAG"]
        featured["result_label"] = featured["FTR"].map(
            {"H": "Home Win", "D": "Draw", "A": "Away Win"}
        )
        featured["high_scoring"] = featured["total_goals"] >= 4
        featured["shot_difference"] = featured["HS"] - featured["AS"]
        featured["sot_difference"] = featured["HST"] - featured["AST"]
        if {"HS", "AS"}.issubset(featured.columns):
            featured["total_shots"] = featured["HS"] + featured["AS"]
        if {"HST", "AST"}.issubset(featured.columns):
            featured["total_shots_on_target"] = featured["HST"] + featured["AST"]
        if {"HC", "AC"}.issubset(featured.columns):
            featured["total_corners"] = featured["HC"] + featured["AC"]
        return featured

    def analyze_home_advantage(self, data: pd.DataFrame) -> pd.DataFrame:
        """Summarize home wins, draws, and away wins for the P6 question."""
        if "FTR" not in data.columns:
            raise ValueError("Home-advantage analysis requires the FTR column.")
        order = ["H", "D", "A"]
        counts = data["FTR"].value_counts().reindex(order, fill_value=0)
        labels = {"H": "Home win", "D": "Draw", "A": "Away win"}
        result = pd.DataFrame(
            {
                "Result": [labels[code] for code in order],
                "Matches": counts.to_numpy(),
                "Share (%)": (counts / max(len(data), 1) * 100).to_numpy(),
            }
        )
        return result

    def analyze_team_performance(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate goals and available shooting statistics by team."""
        required = {"HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"Team analysis requires columns: {', '.join(missing)}")

        home = pd.DataFrame({"Team": data["HomeTeam"], "Goals": data["FTHG"]})
        away = pd.DataFrame({"Team": data["AwayTeam"], "Goals": data["FTAG"]})
        for stat, home_column, away_column in (
            ("Shots", "HS", "AS"),
            ("Shots on target", "HST", "AST"),
        ):
            if {home_column, away_column}.issubset(data.columns):
                home[stat] = data[home_column]
                away[stat] = data[away_column]

        combined = pd.concat([home, away], ignore_index=True)
        summary = combined.groupby("Team").agg(Appearances=("Team", "size"))
        for column in combined.columns:
            if column != "Team":
                summary[column] = combined.groupby("Team")[column].sum(min_count=1)
                summary[f"{column} per appearance"] = summary[column] / summary["Appearances"]
        return summary.sort_values(["Goals", "Goals per appearance"], ascending=False)

    def analyze_goal_distribution(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return descriptive statistics for total goals per completed match."""
        required = {"FTHG", "FTAG"}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"Goal analysis requires columns: {', '.join(missing)}")
        goals = pd.to_numeric(data["FTHG"], errors="coerce") + pd.to_numeric(
            data["FTAG"], errors="coerce"
        )
        goals = goals.dropna()
        if goals.empty:
            raise ValueError("Goal analysis requires at least one completed match.")
        return pd.DataFrame(
            {
                "Metric": ["Mean", "Median", "Standard deviation", "Minimum", "Maximum", "4+ goals (%)"],
                "Value": [
                    goals.mean(),
                    goals.median(),
                    goals.std(ddof=1) if len(goals) > 1 else 0.0,
                    goals.min(),
                    goals.max(),
                    goals.ge(4).mean() * 100,
                ],
            }
        )

    def analyze_match_statistics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return Pearson correlations for available match-statistic totals."""
        required = {"FTHG", "FTAG", "HS", "AS", "HST", "AST", "HC", "AC"}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"Match-statistics analysis requires columns: {', '.join(missing)}")
        totals = pd.DataFrame(
            {
                "Total goals": data["FTHG"] + data["FTAG"],
                "Total shots": data["HS"] + data["AS"],
                "Shots on target": data["HST"] + data["AST"],
                "Corners": data["HC"] + data["AC"],
            }
        )
        return totals.corr(numeric_only=True)

    def export_processed_data(self, data: pd.DataFrame, path: Path) -> None:
        """Export processed data without allowing writes to immutable raw data."""
        destination = path.resolve()
        raw_directory = (Path(__file__).resolve().parents[1] / "data" / "raw").resolve()
        if raw_directory == destination.parent or raw_directory in destination.parents:
            raise ValueError("Processed data cannot be exported under data/raw/.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(destination, index=False)

    def export_results(
        self,
        cleaned_matches: pd.DataFrame,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Export the two required P6 processed datasets."""
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        cleaned_path = destination / "cleaned_matches.csv"
        team_summary_path = destination / "team_summary.csv"
        self.export_processed_data(cleaned_matches, cleaned_path)
        self.export_processed_data(
            self.analyze_team_performance(cleaned_matches), team_summary_path
        )
        return cleaned_path, team_summary_path
