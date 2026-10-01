"""Analysis interfaces to be implemented only in the planned analysis phase."""

from typing import Any


def _not_ready() -> None:
    raise NotImplementedError("Analysis is outside Day 1 scope.")


def analyze_home_advantage(data: Any) -> Any:
    """Reserve RQ1 analysis."""
    _not_ready()


def analyze_team_performance(data: Any) -> Any:
    """Reserve RQ2 analysis."""
    _not_ready()


def analyze_goal_distribution(data: Any) -> Any:
    """Reserve RQ4 analysis."""
    _not_ready()


def analyze_halftime_fulltime(data: Any) -> Any:
    """Reserve RQ3 analysis."""
    _not_ready()


def analyze_match_statistics(data: Any) -> Any:
    """Reserve RQ5 analysis."""
    _not_ready()
