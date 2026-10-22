"""Tests for the comprehensive team analytics extension."""
import unittest
import numpy as np
import pandas as pd
from src.team_analytics import team_match_records, team_summary, season_summary, head_to_head


class TeamAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.matches = pd.DataFrame([
            dict(Season="2025/26", Date="2025-08-01", HomeTeam="Alpha", AwayTeam="Beta",
                 FTHG=1, FTAG=2, HTHG=1, HTAG=0, HS=15, AS=5, HST=6, AST=3),
            dict(Season="2025/26", Date="2025-08-08", HomeTeam="Beta", AwayTeam="Alpha",
                 FTHG=0, FTAG=0, HTHG=0, HTAG=0, HS=np.nan, AS=np.nan, HST=np.nan, AST=np.nan),
        ])
        self.records = team_match_records(self.matches)

    def test_two_rows_per_match(self):
        self.assertEqual(len(self.records), 4)
        self.assertEqual(self.records.groupby("MatchID").size().tolist(), [2, 2])

    def test_wins_losses_and_goals(self):
        summary = team_summary(self.records).set_index("Team")
        self.assertEqual(summary.loc["Alpha", "Losses"], 1)
        self.assertEqual(summary.loc["Beta", "Wins"], 1)
        self.assertEqual(summary.loc["Alpha", "GoalsAgainst"], 2)
        self.assertEqual(summary.loc["Beta", "GoalsFor"], 2)

    def test_comeback_and_lost_lead(self):
        summary = team_summary(self.records).set_index("Team")
        self.assertEqual(summary.loc["Beta", "ComebackWins"], 1)
        self.assertEqual(summary.loc["Alpha", "LostLeads"], 1)
        self.assertEqual(summary.loc["Alpha", "LossesDespiteMoreShots"], 1)
        self.assertEqual(summary.loc["Beta", "ComebackSuccessRate"], 100)

    def test_missing_shots_not_counted_as_zero(self):
        summary = team_summary(self.records).set_index("Team")
        self.assertEqual(summary.loc["Alpha", "ShotDataCoverage"], 50)
        self.assertEqual(summary.loc["Alpha", "Shots"], 15)

    def test_venue_and_season_and_head_to_head(self):
        self.assertEqual(len(team_summary(self.records, by_venue=True)), 4)
        self.assertEqual(season_summary(self.records).iloc[0]["Matches"], 2)
        self.assertEqual(len(head_to_head(self.records, "Alpha", "Beta")), 2)

    def test_required_columns(self):
        with self.assertRaises(ValueError):
            team_match_records(pd.DataFrame({"Season": ["2025/26"]}))


if __name__ == "__main__":
    unittest.main()
