"""Refresh the T13 figures and generate a data-backed T15 mini report."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.analysis import generate_all_visualizations
from src.data_pipeline import clean_matches, create_features, load_raw_csvs
from src.reporting import write_final_report


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "report" / "final_report.md"


def main() -> None:
    raw, raw_files = load_raw_csvs(ROOT / "data" / "raw")
    cleaned, clean_counts = clean_matches(raw)
    if cleaned.empty:
        raise ValueError("No completed matches were found in data/raw/.")
    matches = create_features(cleaned)
    print(f"Loaded {len(raw_files)} season CSV file(s); retained {clean_counts['clean_rows']:,} completed matches")
    # Compute the report's chart summaries in a temporary folder so existing
    # T13 chart files are not replaced by this T15 report command.
    with TemporaryDirectory(prefix="p6_t15_report_") as temporary_charts:
        summaries = generate_all_visualizations(matches, Path(temporary_charts))
    report_path = write_final_report(matches, summaries, REPORT_PATH)
    print(f"Wrote data-backed report: {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
