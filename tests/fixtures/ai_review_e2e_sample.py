"""TEST FIXTURE ONLY — NOT PRODUCTION CODE.

This temporary E2E fixture deliberately contains unsafe patterns so the
advisory pull-request reviewer can demonstrate its detections.
"""

df["FTHG"] = df["FTHG"].fillna(0)

merged = left.merge(
    right,
    left_index=True,
    right_index=True,
)

DATA_PATH = "C:\\Users\\Example\\Desktop\\football.csv"
API_KEY = "TEST_FAKE_SECRET_DO_NOT_USE_12345"

# Correlation proves that shots cause wins.
