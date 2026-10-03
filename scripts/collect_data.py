"""Collect verified Football-Data EPL CSV seasons into immutable raw files."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection import SEASON_CODES, collect_season, inspect_records, save_raw_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        nargs="+",
        choices=tuple(SEASON_CODES),
        default=tuple(SEASON_CODES),
        help="Seasons to collect (default: all verified target seasons).",
    )
    arguments = parser.parse_args()

    for season in arguments.seasons:
        season_code = SEASON_CODES[season]
        destination = ROOT / "data" / "raw" / f"epl_{season_code}_raw.csv"
        try:
            records = collect_season(season)
            audit = inspect_records(records)
            save_raw_data(records, destination)
        except (OSError, RuntimeError, ValueError) as error:
            print(f"Collection failed for {season}: {error}", file=sys.stderr)
            return 1

        print(f"Saved {season}: {audit['row_count']} raw rows -> {destination.relative_to(ROOT)}")
        print(f"Incomplete fixtures: {audit['incomplete_fixtures']}")
        print(f"Duplicate match keys: {len(audit['duplicate_keys'])}")
        nonzero_blanks = {key: value for key, value in audit["blank_values"].items() if value}
        print(f"Columns with blank values: {nonzero_blanks or 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())