from scripts.ai_review.reviewer import provider_findings


def test_missing_credentials_never_calls_provider(monkeypatch) -> None:
    for name in ("AI_REVIEW_API_KEY", "AI_REVIEW_PROVIDER", "AI_REVIEW_MODEL", "AI_REVIEW_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    findings, note = provider_findings({}, "")
    assert findings == []
    assert "skipped" in note


def test_malformed_provider_output_is_reported_safely(monkeypatch) -> None:
    class Response:
        def read(self) -> bytes:
            return b'{"choices":[{"message":{"content":"not-json"}}]}'

    monkeypatch.setenv("AI_REVIEW_API_KEY", "test-only-key")
    monkeypatch.setenv("AI_REVIEW_PROVIDER", "test-provider")
    monkeypatch.setenv("AI_REVIEW_MODEL", "test-model")
    monkeypatch.setenv("AI_REVIEW_ENDPOINT", "https://example.invalid/review")
    monkeypatch.setattr("scripts.ai_review.reviewer.request.urlopen", lambda *args, **kwargs: Response())
    findings, note = provider_findings({}, "diff")
    assert findings == []
    assert "unavailable" in note
