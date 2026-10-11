"""Refresh the T13 figures and generate a data-backed T15 mini report."""

from __future__ import annotations

from pathlib import Path

from src.analysis import generate_all_visualizations
from src.processor import FootballDataProcessor
from src.reporting import write_final_report


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "report" / "final_report.md"
CHARTS_PATH = ROOT / "charts"


def main() -> None:
    processor = FootballDataProcessor()
    raw, raw_files = processor.load_csvs(ROOT / "data" / "raw")
    cleaned = processor.clean_data(raw)
    if cleaned.empty:
        raise ValueError("No completed matches were found in data/raw/.")
    cleaned = processor.normalize_team_names(cleaned)
    matches = processor.create_features(cleaned)
    processed_dir = ROOT / "data" / "processed"
    cleaned_path, team_summary_path = processor.export_results(cleaned, processed_dir)
    print(f"Loaded {len(raw_files)} season CSV file(s); retained {len(cleaned):,} completed matches")
    print(f"Wrote processed data: {cleaned_path.relative_to(ROOT)}, {team_summary_path.relative_to(ROOT)}")
    # Refresh the P6 chart suite in the canonical charts directory so the
    # report, charts, and processed CSVs are generated from the same rows.
    summaries = generate_all_visualizations(matches, CHARTS_PATH)
    report_path = write_final_report(matches, summaries, REPORT_PATH)
    print(f"Wrote data-backed report: {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
