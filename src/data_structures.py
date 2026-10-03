"""Intended Python data-structure usage for the project.

Lists hold collections of match records; dictionaries hold structured match or
team statistics; sets identify unique team names; tuples hold immutable season
configuration.
"""

INITIAL_TARGET_SEASONS: tuple[str, ...] = ("2023/24", "2024/25", "2025/26")


def get_unique_team_names(match_records: list[dict[str, str]]) -> set[str]:
    """Return a set of unique team names from a list of match records."""
    return {match["HomeTeam"] for match in match_records}.union(
        {match["AwayTeam"] for match in match_records}
    )


def count_team_matches(match_records: list[dict[str, str]]) -> dict[str, int]:
    """Return a dictionary counting matches played by each team."""
    match_counts: dict[str, int] = {}

    for match in match_records:
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]

        match_counts[home_team] = match_counts.get(home_team, 0) + 1
        match_counts[away_team] = match_counts.get(away_team, 0) + 1

    return match_counts


def create_match_key(match: dict[str, str]) -> tuple[str, str, str, str]:
    """Return a tuple key uniquely identifying a match."""
    return (
        match["Season"],
        match["Date"],
        match["HomeTeam"],
        match["AwayTeam"],
    )
