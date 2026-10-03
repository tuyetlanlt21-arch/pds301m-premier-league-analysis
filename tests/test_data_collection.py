import csv
from unittest.mock import Mock

import pytest
import requests

from src.data_collection import collect_season, fetch_page, inspect_records, parse_matches, save_raw_data


SYNTHETIC_CSV = (
    "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HTR,HS,AS,HST,AST,HC,AC\n"
    "01/08/25,Example Home FC,Example Away FC,2,1,H,1,0,H,10,8,4,2,5,3\n"
    "01/08/25,Example Home FC,Example Away FC,,,,,,,,,,,,\n"
)


def test_parse_matches_preserves_incomplete_fixture() -> None:
    records = parse_matches(SYNTHETIC_CSV, "2025/26")

    assert len(records) == 2
    assert records[0]["FTHG"] == "2"
    assert records[1]["FTHG"] == ""
    assert records[1]["Season"] == "2025/26"


def test_parse_matches_rejects_missing_required_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        parse_matches("Date,HomeTeam,AwayTeam\n01/08/25,Home,Away\n", "2025/26")


def test_parse_matches_rejects_unsupported_season() -> None:
    with pytest.raises(ValueError, match="Unsupported season"):
        parse_matches(SYNTHETIC_CSV, "2022/23")


@pytest.mark.parametrize(
    ("csv_text", "error_message"),
    [
        ("", "missing its header"),
        (SYNTHETIC_CSV.splitlines()[0] + "\n", "no match rows"),
        (SYNTHETIC_CSV.splitlines()[0] + "\n01/08/25,Home,Away,1\n", "row 2"),
        (
            SYNTHETIC_CSV.splitlines()[0] + "\n,Home,Away,2,1,H,1,0,H,10,8,4,2,5,3\n",
            "missing its date or team name",
        ),
    ],
)
def test_parse_matches_rejects_invalid_or_incomplete_input(csv_text: str, error_message: str) -> None:
    with pytest.raises(ValueError, match=error_message):
        parse_matches(csv_text, "2025/26")


def test_fetch_page_wraps_http_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("503 Server Error")
    monkeypatch.setattr("src.data_collection.requests.get", lambda *args, **kwargs: response)

    with pytest.raises(RuntimeError, match="Failed to fetch source URL"):
        fetch_page("https://example.invalid/matches.csv")


def test_fetch_page_enforces_minimum_request_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    response = Mock(text="csv content")
    monkeypatch.setattr("src.data_collection.requests.get", lambda *args, **kwargs: response)
    monkeypatch.setattr("src.data_collection._last_request_started", 100.0)
    monkeypatch.setattr("src.data_collection.time.monotonic", lambda: 100.25)
    mocked_sleep = Mock()
    monkeypatch.setattr("src.data_collection.time.sleep", mocked_sleep)

    assert fetch_page("https://example.invalid/matches.csv") == "csv content"

    mocked_sleep.assert_called_once_with(0.75)


def test_collect_season_adds_source_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.data_collection.fetch_page", lambda url: SYNTHETIC_CSV)

    records = collect_season("2025/26")

    assert records[0]["Season"] == "2025/26"
    assert records[0]["Source"] == "Football-Data"
    assert records[0]["SourceURL"] == "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
    assert records[0]["CollectionMethod"] == "HTTP CSV download via requests"
    assert records[0]["RetrievedAt"]
    assert records[0]["RetrievedAt"] == records[1]["RetrievedAt"]


def test_inspect_records_reports_duplicates_blanks_and_incomplete_fixtures() -> None:
    records = parse_matches(SYNTHETIC_CSV, "2025/26")

    audit = inspect_records(records)

    assert audit["row_count"] == 2
    assert audit["incomplete_fixtures"] == 1
    assert audit["duplicate_keys"] == [("2025/26", "01/08/25", "Example Home FC", "Example Away FC")]
    assert audit["blank_values"]["FTHG"] == 1
    assert len(records) == 2


def test_save_raw_data_writes_once_with_provenance(tmp_path) -> None:
    records = collect_season_with_mocked_fetch()
    destination = tmp_path / "raw" / "matches.csv"

    save_raw_data(records, destination)

    with destination.open(encoding="utf-8", newline="") as source_file:
        saved_records = list(csv.DictReader(source_file))
    assert saved_records[0]["Source"] == "Football-Data"
    assert saved_records[1]["FTHG"] == ""
    with pytest.raises(FileExistsError):
        save_raw_data(records, destination)


def collect_season_with_mocked_fetch() -> list[dict[str, str]]:
    from unittest.mock import patch

    with patch("src.data_collection.fetch_page", return_value=SYNTHETIC_CSV):
        return collect_season("2025/26")