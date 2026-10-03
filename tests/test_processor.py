"""Focused tests for the T06 cleaning and validation pipeline."""

from pathlib import Path

import pandas as pd
import pytest
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from src.processor import FootballDataProcessor, NUMERIC_COLUMNS, REQUIRED_COLUMNS


def valid_records() -> list[dict[str, object]]:
    base = {
        "Season": "2023/24",
        "Date": "11/08/2023",
        "HomeTeam": "Man City",
        "AwayTeam": "Arsenal",
        "FTHG": "2",
        "FTAG": "1",
        "FTR": "H",
        "HTHG": "1",
        "HTAG": "0",
        "HTR": "H",
        "HS": "12",
        "AS": "8",
        "HST": "5",
        "AST": "3",
        "HC": "6",
        "AC": "4",
        "Source": "Football-Data",
        "CollectionMethod": "HTTP CSV download via requests",
        "SourceURL": "https://example.test/E0.csv",
        "RetrievedAt": "2026-10-02T15:14:52+00:00",
    }
    return [base]


@pytest.fixture
def processor() -> FootballDataProcessor:
    return FootballDataProcessor()


def test_load_data_returns_csv_data_without_changing_source(processor: FootballDataProcessor) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "raw" / "epl_2324_raw.csv"
    original_bytes = source.read_bytes()

    loaded = processor.load_data(source)

    assert len(loaded) == 380
    assert loaded.loc[0, "HomeTeam"] == "Burnley"
    assert source.read_bytes() == original_bytes


def test_validate_data_accepts_complete_schema(processor: FootballDataProcessor) -> None:
    data = pd.DataFrame(valid_records())

    assert processor.validate_data(data) is data


def test_validate_data_rejects_identical_home_and_away_teams(
    processor: FootballDataProcessor,
) -> None:
    data = pd.DataFrame([valid_records()[0] | {"HomeTeam": "Arsenal", "AwayTeam": " Arsenal "}])

    with pytest.raises(ValueError, match="HomeTeam and AwayTeam must be different"):
        processor.validate_data(data)


def test_validate_data_accepts_different_home_and_away_teams(
    processor: FootballDataProcessor,
) -> None:
    data = pd.DataFrame(valid_records())

    assert processor.validate_data(data) is data


@pytest.mark.parametrize("numeric_column", NUMERIC_COLUMNS)
def test_validate_data_rejects_negative_numeric_values(
    processor: FootballDataProcessor, numeric_column: str
) -> None:
    data = pd.DataFrame([valid_records()[0] | {numeric_column: "-1"}])

    with pytest.raises(ValueError, match=f"Numeric column {numeric_column} cannot contain negative values"):
        processor.validate_data(data)


def test_validate_data_accepts_zero_for_numeric_fields(processor: FootballDataProcessor) -> None:
    record = valid_records()[0] | {column: "0" for column in NUMERIC_COLUMNS}
    data = pd.DataFrame([record])

    assert processor.validate_data(data) is data


def test_validate_data_preserves_missing_numeric_values(
    processor: FootballDataProcessor,
) -> None:
    record = valid_records()[0] | {column: None for column in NUMERIC_COLUMNS}
    data = pd.DataFrame([record])
    original = data.copy(deep=True)

    validated = processor.validate_data(data)

    assert validated is data
    pd.testing.assert_frame_equal(data, original)
    assert data[list(NUMERIC_COLUMNS)].isna().all().all()


def test_validate_data_rejects_missing_required_column(
    processor: FootballDataProcessor,
) -> None:
    data = pd.DataFrame(valid_records()).drop(columns="HC")

    with pytest.raises(ValueError, match="required columns"):
        processor.validate_data(data)


@pytest.mark.parametrize("identity_column", ["Season", "Date", "HomeTeam", "AwayTeam"])
def test_validate_data_rejects_missing_fixture_identity(
    processor: FootballDataProcessor, identity_column: str
) -> None:
    data = pd.DataFrame(valid_records())
    data.loc[0, identity_column] = None

    with pytest.raises(ValueError, match=identity_column):
        processor.validate_data(data)


def test_clean_data_parses_date_and_numeric_columns(processor: FootballDataProcessor) -> None:
    cleaned = processor.clean_data(pd.DataFrame(valid_records()))

    assert is_datetime64_any_dtype(cleaned["Date"])
    for column in ("FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST", "HC", "AC"):
        assert is_numeric_dtype(cleaned[column])
    assert cleaned.loc[cleaned.index[0], "Date"] == pd.Timestamp("2023-08-11")


def test_clean_data_excludes_incomplete_fixture_without_zero_filling(
    processor: FootballDataProcessor,
) -> None:
    incomplete = valid_records()[0] | {"FTHG": None, "FTAG": None, "FTR": ""}
    data = pd.DataFrame(valid_records() + [incomplete])

    cleaned = processor.clean_data(data)

    assert len(cleaned) == 1
    assert pd.isna(data.loc[1, "FTHG"])
    assert pd.isna(data.loc[1, "FTAG"])
    assert not (cleaned[["FTHG", "FTAG"]] == 0).all(axis=1).any()


def test_clean_data_keeps_first_duplicate_by_full_fixture_identity(
    processor: FootballDataProcessor,
) -> None:
    first = valid_records()[0]
    duplicate = first | {"HS": "99"}
    same_teams_different_date = first | {"Date": "12/08/2023", "HS": "77"}

    cleaned = processor.clean_data(pd.DataFrame([first, duplicate, same_teams_different_date]))

    assert len(cleaned) == 2
    assert cleaned.iloc[0]["HS"] == 12
    assert cleaned.iloc[1]["HS"] == 77


@pytest.mark.parametrize(
    ("home_goals", "away_goals", "result"),
    [("2", "1", "H"), ("1", "1", "D"), ("0", "2", "A")],
)
def test_clean_data_accepts_consistent_completed_results(
    processor: FootballDataProcessor, home_goals: str, away_goals: str, result: str
) -> None:
    record = valid_records()[0] | {"FTHG": home_goals, "FTAG": away_goals, "FTR": result}

    assert len(processor.clean_data(pd.DataFrame([record]))) == 1


def test_clean_data_rejects_inconsistent_completed_result(
    processor: FootballDataProcessor,
) -> None:
    data = pd.DataFrame([valid_records()[0] | {"FTHG": "2", "FTAG": "1", "FTR": "A"}])

    with pytest.raises(ValueError, match="inconsistent"):
        processor.clean_data(data)


def test_clean_data_does_not_mutate_input(processor: FootballDataProcessor) -> None:
    data = pd.DataFrame(valid_records())
    original = data.copy(deep=True)

    processor.clean_data(data)

    pd.testing.assert_frame_equal(data, original)


def test_clean_data_handles_empty_data_with_schema(processor: FootballDataProcessor) -> None:
    empty = pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    cleaned = processor.clean_data(empty)

    assert cleaned.empty
    assert is_datetime64_any_dtype(cleaned["Date"])


def test_normalize_team_names_strips_aliases_and_preserves_unknown_names(
    processor: FootballDataProcessor,
) -> None:
    data = pd.DataFrame(
        [
            valid_records()[0]
            | {"HomeTeam": "  Man City ", "AwayTeam": "  Arsenal  "},
        ]
    )

    normalized = processor.normalize_team_names(data)

    assert normalized.loc[0, "HomeTeam"] == "Manchester City"
    assert normalized.loc[0, "AwayTeam"] == "Arsenal"
    assert data.loc[0, "HomeTeam"] == "  Man City "
    assert data.loc[0, "AwayTeam"] == "  Arsenal  "


def feature_records() -> pd.DataFrame:
    home_win = valid_records()[0] | {
        "FTHG": 2,
        "FTAG": 1,
        "FTR": "H",
        "HS": 12,
        "AS": 8,
        "HST": 5,
        "AST": 3,
    }
    draw = home_win | {
        "Date": "12/08/2023",
        "FTHG": 2,
        "FTAG": 2,
        "FTR": "D",
        "HS": 9,
        "AS": 9,
        "HST": 4,
        "AST": 4,
    }
    away_win = home_win | {
        "Date": "13/08/2023",
        "FTHG": 1,
        "FTAG": 3,
        "FTR": "A",
        "HS": 7,
        "AS": 14,
        "HST": 2,
        "AST": 6,
    }
    return pd.DataFrame([home_win, draw, away_win])


def test_create_features_adds_all_documented_derived_columns(
    processor: FootballDataProcessor,
) -> None:
    featured = processor.create_features(feature_records())

    assert featured["total_goals"].tolist() == [3, 4, 4]
    assert featured["goal_difference"].tolist() == [1, 0, -2]
    assert featured["result_label"].tolist() == ["Home Win", "Draw", "Away Win"]
    assert featured["high_scoring"].tolist() == [False, True, True]
    assert featured["shot_difference"].tolist() == [4, 0, -7]
    assert featured["sot_difference"].tolist() == [2, 0, -4]


def test_create_features_does_not_mutate_input(processor: FootballDataProcessor) -> None:
    data = feature_records()
    original = data.copy(deep=True)

    processor.create_features(data)

    pd.testing.assert_frame_equal(data, original)


def test_export_processed_data_creates_parent_and_omits_index(
    processor: FootballDataProcessor, tmp_path
) -> None:
    destination = tmp_path / "processed" / "matches.csv"
    featured = processor.create_features(feature_records())

    processor.export_processed_data(featured, destination)

    exported = pd.read_csv(destination)
    assert destination.is_file()
    assert "Unnamed: 0" not in exported.columns
    assert exported["total_goals"].tolist() == [3, 4, 4]


def test_export_processed_data_rejects_raw_data_destination(
    processor: FootballDataProcessor,
) -> None:
    raw_destination = Path(__file__).resolve().parents[1] / "data" / "raw" / "new.csv"

    with pytest.raises(ValueError, match="data/raw"):
        processor.export_processed_data(feature_records(), raw_destination)


def test_processor_methods_complete_the_raw_to_processed_workflow(
    processor: FootballDataProcessor, tmp_path
) -> None:
    raw_path = tmp_path / "raw" / "matches.csv"
    raw_path.parent.mkdir()
    pd.DataFrame(valid_records()).to_csv(raw_path, index=False)
    raw_bytes = raw_path.read_bytes()
    processed_path = tmp_path / "processed" / "matches.csv"

    loaded = processor.load_data(raw_path)
    validated = processor.validate_data(loaded)
    cleaned = processor.clean_data(validated)
    normalized = processor.normalize_team_names(cleaned)
    featured = processor.create_features(normalized)
    processor.export_processed_data(featured, processed_path)

    exported = pd.read_csv(processed_path)
    assert raw_path.read_bytes() == raw_bytes
    assert exported.loc[0, "HomeTeam"] == "Manchester City"
    assert exported.loc[0, "total_goals"] == 3
    assert exported.loc[0, "result_label"] == "Home Win"
    assert "Unnamed: 0" not in exported.columns
