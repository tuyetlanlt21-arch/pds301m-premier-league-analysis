from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd

from scripts.generate_visualizations import write_visualization_insights
from src.analysis import analyze_home_advantage, analyze_match_statistics, generate_all_visualizations


def sample_matches() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Season": ["2023/24"] * 4 + ["2024/25"] * 4,
            "HomeTeam": ["Arsenal", "Chelsea", "Liverpool", "Spurs"] * 2,
            "AwayTeam": ["Chelsea", "Spurs", "Arsenal", "Liverpool"] * 2,
            "FTHG": [2, 0, 3, 1, 1, 2, 0, 4],
            "FTAG": [1, 0, 1, 2, 2, 1, 1, 0],
            "FTR": ["H", "D", "H", "A", "A", "H", "A", "H"],
            "HTR": ["D", "D", "H", "A", "A", "H", "D", "D"],
            "HS": [12, 8, 16, 10, 15, 11, 7, 20],
            "AS": [7, 9, 8, 13, 12, 10, 14, 6],
            "HST": [5, 3, 7, 4, 6, 4, 2, 9],
            "AST": [3, 4, 3, 6, 5, 5, 6, 2],
            "HC": [6, 4, 8, 5, 7, 5, 3, 10],
            "AC": [3, 5, 4, 7, 6, 4, 8, 2],
        }
    )


class VisualizationTests(unittest.TestCase):
    def test_full_chart_suite_writes_eight_charts_and_preserves_input(self):
        matches = sample_matches()
        original = matches.copy(deep=True)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            results = generate_all_visualizations(matches, output)
            charts = list(output.glob("*.png"))

            self.assertEqual(len(results), 8)
            self.assertEqual(len(charts), 8)
            self.assertTrue(all(path.stat().st_size > 0 for path in charts))
            self.assertTrue(math.isclose(float(results["home_advantage"].sum()), 100.0))
            self.assertEqual(list(results["halftime_fulltime"].index), ["Home win", "Draw", "Away win"])
            pd.testing.assert_frame_equal(matches, original)

    def test_insights_report_has_evidence_for_each_chart(self):
        matches = sample_matches()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            summaries = generate_all_visualizations(matches, output)
            report_path = write_visualization_insights(matches, summaries, output)
            report = report_path.read_text(encoding="utf-8")

            self.assertEqual(report.count("**Evidence-based insight:**"), 8)
            self.assertIn("8 completed matches", report)
            self.assertIn("home_advantage_outcomes.png", report)

    def test_home_advantage_accepts_feature_engineered_result_labels(self):
        matches = sample_matches()
        featured = matches.assign(
            result_label=matches["FTR"].map({"H": "Home Win", "D": "Draw", "A": "Away Win"})
        )
        with tempfile.TemporaryDirectory() as directory:
            rates = analyze_home_advantage(featured.drop(columns="FTR"), directory)

        self.assertEqual(float(rates["Home win"]), 50.0)
        self.assertEqual(float(rates["Draw"]), 12.5)
        self.assertEqual(float(rates["Away win"]), 37.5)

    def test_statistics_chart_reports_missing_required_columns(self):
        matches = sample_matches().drop(columns="HST")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "HST"):
                analyze_match_statistics(matches, directory)


if __name__ == "__main__":
    unittest.main()
