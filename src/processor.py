"""Validation, cleaning, and team-name normalization for raw match data."""

from pathlib import Path
from typing import Any

import pandas as pd

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
        return featured

    def export_processed_data(self, data: pd.DataFrame, path: Path) -> None:
        """Export processed data without allowing writes to immutable raw data."""
        destination = path.resolve()
        raw_directory = (Path(__file__).resolve().parents[1] / "data" / "raw").resolve()
        if raw_directory == destination.parent or raw_directory in destination.parents:
            raise ValueError("Processed data cannot be exported under data/raw/.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(destination, index=False)
