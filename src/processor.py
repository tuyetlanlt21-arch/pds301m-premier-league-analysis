"""Data-processing interfaces; implementations are deliberately deferred."""

from pathlib import Path
from typing import Any


class FootballDataProcessor:
    """Define the intended raw-to-processed data lifecycle."""

    def load_data(self, path: Path) -> Any:
        """Reserve loading a collected raw dataset."""
        raise NotImplementedError("Processing begins after data collection.")

    def validate_data(self, data: Any) -> Any:
        """Reserve validation against the documented contract and rules."""
        raise NotImplementedError("Processing begins after data collection.")

    def clean_data(self, data: Any) -> Any:
        """Reserve cleaning of validated data."""
        raise NotImplementedError("Processing begins after data collection.")

    def normalize_team_names(self, data: Any) -> Any:
        """Reserve team-name normalization before multi-source integration."""
        raise NotImplementedError("Processing begins after data collection.")

    def create_features(self, data: Any) -> Any:
        """Reserve documented feature engineering."""
        raise NotImplementedError("Processing begins after data collection.")

    def export_processed_data(self, data: Any, path: Path) -> None:
        """Reserve export of processed data to a repository-relative path."""
        raise NotImplementedError("Processing begins after data collection.")
