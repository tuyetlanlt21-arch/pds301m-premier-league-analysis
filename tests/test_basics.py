"""Tests use synthetic educational values only, never match records."""

from src.basics import calculate_points, calculate_total_goals, classify_goal_match, map_result


def test_basic_helpers() -> None:
    assert calculate_total_goals(2, 1) == 3
    assert map_result("H") == "Home Win"
    assert calculate_points("D") == (1, 1)
    assert classify_goal_match(4) == "High scoring"
