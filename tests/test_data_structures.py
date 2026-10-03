"""Tests for T05 list, dictionary, set, and tuple helpers."""

from src.data_structures import (
    INITIAL_TARGET_SEASONS,
    count_team_matches,
    create_match_key,
    get_unique_team_names,
)


MATCH_RECORDS = [
    {
        "Season": "2023/24",
        "Date": "11/08/2023",
        "HomeTeam": "Burnley",
        "AwayTeam": "Man City",
    },
    {
        "Season": "2023/24",
        "Date": "12/08/2023",
        "HomeTeam": "Man City",
        "AwayTeam": "Arsenal",
    },
]


def test_initial_target_seasons_is_an_immutable_tuple() -> None:
    assert INITIAL_TARGET_SEASONS == ("2023/24", "2024/25", "2025/26")


def test_get_unique_team_names_handles_repeated_teams_and_empty_input() -> None:
    assert get_unique_team_names(MATCH_RECORDS) == {"Burnley", "Man City", "Arsenal"}
    assert get_unique_team_names([]) == set()


def test_count_team_matches_counts_home_and_away_appearances() -> None:
    assert count_team_matches(MATCH_RECORDS) == {
        "Burnley": 1,
        "Man City": 2,
        "Arsenal": 1,
    }
    assert count_team_matches([]) == {}


def test_create_match_key_uses_the_documented_contract_order() -> None:
    assert create_match_key(MATCH_RECORDS[0]) == (
        "2023/24",
        "11/08/2023",
        "Burnley",
        "Man City",
    )
