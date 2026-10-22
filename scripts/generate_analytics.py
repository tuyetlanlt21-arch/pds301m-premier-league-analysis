"""Build the complete website-ready analytics data contract and charts."""

from __future__ import annotations

from pathlib import Path

from src.analytics import build_analytics, export_analytics
from src.analytics_visuals import generate_expanded_visualizations
from src.data_pipeline import load_raw_csvs

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw, paths = load_raw_csvs(ROOT / "data" / "raw")
    bundle = build_analytics(raw)
    export_dir = ROOT / "data" / "processed" / "analytics"
    written = export_analytics(bundle, export_dir)
    charts = generate_expanded_visualizations(bundle, ROOT / "charts")
    print(f"Loaded {len(paths)} raw season file(s); retained {len(bundle['cleaned_matches']):,} completed matches")
    print(f"Exported {len(written)} CSV/JSON files to {export_dir.relative_to(ROOT)}")
    print(f"Generated {len(charts)} expanded charts in charts/")


if __name__ == "__main__":
    main()
