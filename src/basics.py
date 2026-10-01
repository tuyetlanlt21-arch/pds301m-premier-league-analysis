"""Small, reusable Python-basics helpers for later project phases."""


def calculate_total_goals(home_goals: int, away_goals: int) -> int:
    """Return the combined goals for a completed match."""
    return home_goals + away_goals


def map_result(result_code: str) -> str:
    """Map a final-result code to its descriptive label."""
    labels = {"H": "Home Win", "D": "Draw", "A": "Away Win"}
    return labels[result_code]


def calculate_points(result_code: str) -> tuple[int, int]:
    """Return (home_points, away_points) for a final-result code."""
    points = {"H": (3, 0), "D": (1, 1), "A": (0, 3)}
    return points[result_code]


def classify_goal_match(total_goals: int) -> str:
    """Classify a match as high scoring when it has four or more goals."""
    return "High scoring" if total_goals >= 4 else "Standard scoring"
