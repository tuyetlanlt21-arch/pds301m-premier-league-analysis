"""Collect EPL match CSVs from verified Football-Data season URLs."""

import csv
from collections import Counter
from datetime import datetime, timezone
import io
from pathlib import Path
import threading
import time
from typing import Any

import requests


SOURCE_NAME = "Football-Data"
SOURCE_URL_TEMPLATE = "https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv"
SEASON_CODES = {"2023/24": "2324", "2024/25": "2425", "2025/26": "2526"}
REQUIRED_COLUMNS = {
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR",
    "HS", "AS", "HST", "AST", "HC", "AC",
}
PROVENANCE_COLUMNS = ("Season", "Source", "CollectionMethod", "SourceURL", "RetrievedAt")
REQUEST_TIMEOUT_SECONDS = 20
MIN_REQUEST_INTERVAL_SECONDS = 1.0
USER_AGENT = "PremierLeagueCoursework/1.0"
_REQUEST_LOCK = threading.Lock()
_last_request_started: float | None = None


def _wait_for_request_slot() -> None:
    """Keep request start times at least one second apart across callers."""
    global _last_request_started
    with _REQUEST_LOCK:
        now = time.monotonic()
        if _last_request_started is not None:
            wait_seconds = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_started)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
        _last_request_started = time.monotonic()

def fetch_page(url: str) -> str:
    """Fetch one source URL with a timeout and explicit HTTP error handling."""
    _wait_for_request_slot()
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Failed to fetch source URL {url}: {error}") from error

    if not response.text.strip():
        raise ValueError(f"Source URL returned an empty response: {url}")
    return response.text


def parse_matches(page_html: str, season: str) -> list[dict[str, Any]]:
    """Parse a verified season CSV without filling incomplete fixture values."""
    if season not in SEASON_CODES:
        raise ValueError(f"Unsupported season: {season}. Supported seasons: {', '.join(SEASON_CODES)}")

    reader = csv.DictReader(io.StringIO(page_html.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValueError("CSV is missing its header row.")

    reader.fieldnames = [field.strip() for field in reader.fieldnames]
    missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV row {row_number} does not match the header width.")
        if any(not row[field].strip() for field in ("Date", "HomeTeam", "AwayTeam")):
            raise ValueError(f"CSV row {row_number} is missing its date or team name.")
        row["Season"] = season
        records.append(row)

    if not records:
        raise ValueError("CSV contains no match rows.")
    return records


def collect_season(season: str) -> list[dict[str, Any]]:
    """Collect one verified season and attach source provenance to every row."""
    if season not in SEASON_CODES:
        raise ValueError(f"Unsupported season: {season}. Supported seasons: {', '.join(SEASON_CODES)}")

    source_url = SOURCE_URL_TEMPLATE.format(season_code=SEASON_CODES[season])
    page_text = fetch_page(source_url)
    records = parse_matches(page_text, season)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for record in records:
        record.update({
            "Source": SOURCE_NAME,
            "CollectionMethod": "HTTP CSV download via requests",
            "SourceURL": source_url,
            "RetrievedAt": retrieved_at,
        })
    return records


def inspect_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize raw-data gaps and duplicate match keys without changing rows."""
    match_keys = [
        (row.get("Season"), row.get("Date"), row.get("HomeTeam"), row.get("AwayTeam"))
        for row in records
    ]
    key_counts = Counter(match_keys)
    duplicate_keys = sorted(key for key, count in key_counts.items() if count > 1)
    incomplete_fixtures = sum(
        not row.get("FTHG", "").strip()
        or not row.get("FTAG", "").strip()
        or row.get("FTR", "").strip() not in {"H", "D", "A"}
        for row in records
    )
    columns = sorted({column for row in records for column in row})
    blank_values = {
        column: sum(not str(row.get(column, "")).strip() for row in records)
        for column in columns
    }
    return {
        "row_count": len(records),
        "incomplete_fixtures": incomplete_fixtures,
        "duplicate_keys": duplicate_keys,
        "blank_values": blank_values,
    }


def save_raw_data(records: list[dict[str, Any]], destination: Path) -> None:
    """Save provenance-complete raw records without overwriting an existing file."""
    if not records:
        raise ValueError("Cannot save an empty raw dataset.")

    expected_fields = set(records[0])
    if not set(PROVENANCE_COLUMNS).issubset(expected_fields):
        raise ValueError("Raw records are missing required source provenance metadata.")
    if any(set(record) != expected_fields for record in records):
        raise ValueError("Raw records do not share a consistent set of columns.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
