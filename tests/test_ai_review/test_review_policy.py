from scripts.ai_review.diff_parser import parse_unified_diff
import pytest

from scripts.ai_review.models import ReviewResult, Severity
from scripts.ai_review.reviewer import run
from scripts.ai_review.review_policy import evaluate
from scripts.ai_review.rule_loader import load_rules, repository_root


def policy(diff: str):
    return evaluate(parse_unified_diff(diff), load_rules(repository_root()))


def test_missing_goals_are_not_filled_with_zero() -> None:
    findings = policy('diff --git a/src/processor.py b/src/processor.py\n@@ -1 +1 @@\n+df["FTHG"] = df["FTHG"].fillna(0)')
    assert findings[0].severity is Severity.HIGH


def test_index_merge_is_flagged() -> None:
    findings = policy("diff --git a/src/processor.py b/src/processor.py\n@@ -1 +1 @@\n+merged = left.merge(right, left_index=True, right_index=True)")
    assert findings[0].severity is Severity.HIGH


def test_secret_literal_is_critical() -> None:
    findings = policy('diff --git a/src/x.py b/src/x.py\n@@ -1 +1 @@\n+API_KEY = "not-a-real-secret-value"')
    assert findings[0].severity is Severity.CRITICAL


def test_high_finding_is_advisory_blocked_result() -> None:
    review = run('diff --git a/src/x.py b/src/x.py\n@@ -1 +1 @@\n+df["FTAG"] = df["FTAG"].fillna(0)', mock=True)
    assert review.result is ReviewResult.BLOCKED


def test_severity_rejects_unknown_values() -> None:
    with pytest.raises(ValueError):
        Severity("URGENT")
