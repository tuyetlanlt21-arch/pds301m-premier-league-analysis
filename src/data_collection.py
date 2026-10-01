"""Day 2 collection interfaces. Day 1 intentionally makes no HTTP requests."""

from pathlib import Path
from typing import Any


def fetch_page(url: str) -> str:
    """Reserve controlled page retrieval for Day 2 source inspection."""
    raise NotImplementedError("Data collection begins in Day 2.")


def parse_matches(page_html: str, season: str) -> list[dict[str, Any]]:
    """Reserve parsing of a verified source page into match records."""
    raise NotImplementedError("Data collection begins in Day 2.")


def collect_season(season: str) -> list[dict[str, Any]]:
    """Reserve orchestration for one inspected, approved season source."""
    raise NotImplementedError("Data collection begins in Day 2.")


def save_raw_data(records: list[dict[str, Any]], destination: Path) -> None:
    """Reserve saving externally collected records without manual alteration."""
    raise NotImplementedError("Data collection begins in Day 2.")
