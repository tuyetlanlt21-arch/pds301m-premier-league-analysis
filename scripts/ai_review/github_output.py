"""Render a stable, updatable pull-request review comment."""

from .models import Review, Severity


MARKER = "<!-- pds301m-ai-review -->"


def render_markdown(review: Review) -> str:
    """Render concise Markdown suitable for a single stable PR comment."""
    lines = [MARKER, "# Automated Project Review", "", "## Result", "", review.result.value.replace("_", " "), "", "## Summary", ""]
    for severity in Severity:
        lines.append(f"{severity.value.title()}: {review.count(severity)}")
    lines += ["", review.provider_note, "", "## Findings", ""]
    if not review.findings:
        lines.append("No meaningful project-policy findings were detected.")
    for item in review.findings:
        lines += [f"### {item.severity.value} — {item.title}", "", f"**File:** `{item.file}`", f"**Line:** {item.line or 'file-level'}", f"**Rule:** {item.rule}", "", f"**Problem:** {item.problem}", "", f"**Impact:** {item.impact}", "", f"**Suggested fix:** {item.suggested_fix}", "", "---", ""]
    lines += ["## Files Reviewed", "", *[f"- `{path}`" for path in review.files_reviewed], "", "## Rules Consulted", "", *[f"- `{path}`" for path in review.rules_consulted], "", "_Advisory only: this result is not a required branch-protection check._"]
    return "\n".join(lines)
