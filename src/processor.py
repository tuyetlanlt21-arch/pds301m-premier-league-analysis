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

    def create_features(self, data: Any) -> Any:
        """Reserve documented feature engineering."""
        raise NotImplementedError("Processing begins after data collection.")

    def export_processed_data(self, data: Any, path: Path) -> None:
        """Reserve export of processed data to a repository-relative path."""
        raise NotImplementedError("Processing begins after data collection.")
