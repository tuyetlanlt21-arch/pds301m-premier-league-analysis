"""Tests use synthetic educational values only, never match records."""

import pytest

from src.basics import calculate_points, calculate_total_goals, classify_goal_match, map_result


def test_basic_helpers() -> None:
    assert calculate_total_goals(2, 1) == 3


@pytest.mark.parametrize(
    ("result_code", "label", "points"),
    [
        ("H", "Home Win", (3, 0)),
        ("D", "Draw", (1, 1)),
        ("A", "Away Win", (0, 3)),
    ],
)
def test_result_helpers_cover_all_result_codes(
    result_code: str, label: str, points: tuple[int, int]
) -> None:
    assert map_result(result_code) == label
    assert calculate_points(result_code) == points


def test_goal_classification_covers_threshold_boundary() -> None:
    assert classify_goal_match(3) == "Standard scoring"
    assert classify_goal_match(4) == "High scoring"


@pytest.mark.parametrize("helper", [map_result, calculate_points])
def test_result_helpers_reject_unknown_result_code(helper) -> None:
    with pytest.raises(KeyError):
        helper("X")
