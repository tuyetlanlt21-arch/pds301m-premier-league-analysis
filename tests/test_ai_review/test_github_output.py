from scripts.ai_review.github_output import MARKER, render_markdown
from scripts.ai_review.models import Finding, Review, Severity


def test_markdown_has_stable_marker_and_summary() -> None:
    review = Review([Finding(Severity.LOW, "Naming", "src/a.py", 3, "PROJECT_RULES.md", "p", "i", "f")], ["src/a.py"], ["docs/PROJECT_RULES.md"])
    output = render_markdown(review)
    assert output.startswith(MARKER)
    assert "PASS WITH COMMENTS" in output
    assert "Low: 1" in output
