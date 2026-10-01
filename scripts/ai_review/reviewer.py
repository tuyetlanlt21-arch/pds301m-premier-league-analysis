"""CLI for advisory deterministic review with optional provider augmentation."""

import argparse
import json
import os
from pathlib import Path
from urllib import request

from .diff_parser import parse_unified_diff
from .github_output import render_markdown
from .models import Finding, Review, Severity
from .review_policy import evaluate
from .rule_loader import RULE_FILES, load_rules, repository_root


def provider_findings(policy: dict[str, str], diff: str) -> tuple[list[Finding], str]:
    """Call a configured OpenAI-compatible provider; never call it without a key."""
    key = os.getenv("AI_REVIEW_API_KEY")
    provider = os.getenv("AI_REVIEW_PROVIDER")
    model = os.getenv("AI_REVIEW_MODEL")
    endpoint = os.getenv("AI_REVIEW_ENDPOINT")
    if not all((key, provider, model, endpoint)):
        return [], "AI augmentation skipped: AI_REVIEW_API_KEY, AI_REVIEW_PROVIDER, AI_REVIEW_MODEL, and AI_REVIEW_ENDPOINT are not fully configured."
    prompt = "Return JSON only: {findings:[{severity,title,file,line,rule,problem,impact,suggested_fix}]}. Review this project policy and diff.\n" + json.dumps(policy) + "\nDIFF:\n" + diff
    payload = json.dumps({"model": model, "messages": [{"role": "system", "content": "You are an advisory repository reviewer. Do not invent findings."}, {"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}).encode()
    try:
        req = request.Request(endpoint, data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
        response = json.loads(request.urlopen(req, timeout=30).read().decode())
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        findings = [Finding(Severity(item["severity"]), item["title"], item["file"], int(item["line"]), item["rule"], item["problem"], item["impact"], item["suggested_fix"]) for item in parsed.get("findings", [])]
        return findings, f"AI augmentation completed using configured provider `{provider}` and model `{model}`."
    except (KeyError, TypeError, ValueError, OSError) as error:
        return [], f"AI augmentation unavailable: provider response could not be safely parsed ({type(error).__name__})."


def run(diff: str, root: Path | None = None, mock: bool = False) -> Review:
    """Build one advisory review from untrusted diff text and trusted policy files."""
    base = root or repository_root()
    rules = load_rules(base)
    patches = parse_unified_diff(diff)
    findings = evaluate(patches, rules)
    ai_findings, note = ([], "Mock mode: no external AI provider was called.") if mock else provider_findings(rules, diff)
    return Review(findings + ai_findings, [patch.path for patch in patches], list(RULE_FILES), note)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run advisory PDS301M PR review.")
    parser.add_argument("--diff-file", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    review = run(args.diff_file.read_text(encoding="utf-8"), mock=args.mock)
    markdown = render_markdown(review)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
