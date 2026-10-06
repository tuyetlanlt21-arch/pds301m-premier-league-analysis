from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

import pandas as pd

from src.data_pipeline import clean_matches, create_features, load_raw_csvs
from src.reporting import render_final_report


class DataPipelineTests(unittest.TestCase):
    def test_loader_reads_saved_csv_and_infers_season_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "epl_2324_raw.csv"
            original = "Date,HomeTeam,AwayTeam,FTHG,FTAG\n11/08/2023,Arsenal,Burnley,2,1\n"
            path.write_text(original, encoding="utf-8")

            raw, files = load_raw_csvs(directory)

            self.assertEqual([file.name for file in files], ["epl_2324_raw.csv"])
            self.assertEqual(raw.loc[0, "Season"], "2023/24")
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_cleaning_deduplicates_completed_matches_without_changing_input(self):
        raw = pd.DataFrame(
            {
                "Season": ["2023/24", "2023/24", "2023/24", "2023/24"],
                "Date": ["11/08/2023", "11/08/2023", "12/08/2023", "13/08/2023"],
                "HomeTeam": [" Arsenal  ", "Arsenal", "Chelsea", "Liverpool"],
                "AwayTeam": ["Burnley", "Burnley", "Luton", "Bournemouth"],
                "FTHG": [2, 2, None, 1],
                "FTAG": [1, 1, None, 1],
                "FTR": ["A", "A", None, "H"],  # Full-time result is derived from scores.
            }
        )
        original = raw.copy(deep=True)

        cleaned, counts = clean_matches(raw)

        self.assertEqual(counts["raw_rows"], 4)
        self.assertEqual(counts["removed_incomplete_or_invalid"], 1)
        self.assertEqual(counts["removed_duplicates"], 1)
        self.assertEqual(counts["clean_rows"], 2)
        self.assertEqual(cleaned.loc[0, "HomeTeam"], "Arsenal")
        self.assertEqual(cleaned.loc[0, "FTR"], "H")
        self.assertTrue(cleaned["HS"].isna().all())
        pd.testing.assert_frame_equal(raw, original)

    def test_feature_engineering_uses_scores_and_leaves_unavailable_stats_missing(self):
        cleaned, _ = clean_matches(
            pd.DataFrame(
                {
                    "Season": ["2023/24"],
                    "Date": ["11/08/2023"],
                    "HomeTeam": ["Arsenal"],
                    "AwayTeam": ["Burnley"],
                    "FTHG": [3],
                    "FTAG": [1],
                    "FTR": ["H"],
                }
            )
        )
        featured = create_features(cleaned)
        self.assertEqual(featured.loc[0, "total_goals"], 4)
        self.assertEqual(featured.loc[0, "goal_difference"], 2)
        self.assertTrue(featured.loc[0, "high_scoring"])
        self.assertTrue(pd.isna(featured.loc[0, "total_shots"]))


class ReportTests(unittest.TestCase):
    def test_report_uses_supplied_members_and_dataset_findings(self):
        matches = create_features(pd.DataFrame(
            {
                "Season": ["2023/24", "2023/24"],
                "HomeTeam": ["Arsenal", "Chelsea"],
                "AwayTeam": ["Burnley", "Everton"],
                "FTHG": [2, 0],
                "FTAG": [0, 1],
                "FTR": ["H", "A"],
                "HTR": ["H", "D"],
                "HS": [10, 8], "AS": [5, 9],
                "HST": [4, 3], "AST": [2, 5],
            }
        ))
        correlations = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=["Total shots", "Shots on target"],
            columns=["Total shots", "Shots on target"],
        )
        summaries = {
            "home_advantage": pd.Series({"Home win": 50.0, "Draw": 0.0, "Away win": 50.0}),
            "team_performance": pd.Series({"Arsenal": 2, "Chelsea": 0}),
            "halftime_fulltime": pd.DataFrame(
                [[1, 0, 0], [0, 0, 1], [0, 0, 0]],
                index=["Home win", "Draw", "Away win"],
                columns=["Home win", "Draw", "Away win"],
            ),
            "season_comparison": pd.DataFrame(
                [{"Season": "2023/24", "Matches": 2, "MeanGoals": 1.5}]
            ),
            "match_statistics_correlation": correlations,
            "goals_vs_shots": pd.DataFrame({"Total shots": [15, 17], "Total goals": [2, 1]}),
        }

        report = render_final_report(matches, summaries)

        self.assertIn("2 completed matches", report)
        self.assertIn("home wins were 50.0%", report)
        self.assertIn("SE203600 | Lê Thị Tuyết Lan |  |", report)
        self.assertIn("SE190537 | Nguyễn Quốc Toàn |  |", report)
        self.assertNotIn("[Member name]", report)


if __name__ == "__main__":
    unittest.main()
