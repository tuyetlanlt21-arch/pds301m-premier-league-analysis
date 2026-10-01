"""Project-specific, deterministic advisory checks over an untrusted diff."""

import re

from .diff_parser import FilePatch
from .models import Finding, Severity


def _finding(severity: Severity, title: str, patch: FilePatch, line: int, rule: str, problem: str, impact: str, fix: str) -> Finding:
    return Finding(severity, title, patch.path, line, rule, problem, impact, fix)


def evaluate(patches: list[FilePatch], rules: dict[str, str]) -> list[Finding]:
    """Check changed content against risks explicitly covered by project rules."""
    findings: list[Finding] = []
    for patch in patches:
        if patch.path.startswith("data/raw/") and (patch.additions or patch.deleted):
            findings.append(_finding(Severity.CRITICAL, "Raw data change", patch, 0, "PROJECT_RULES.md", "A raw-data file is changed.", "Raw source data must remain immutable.", "Keep source data unchanged; write derived output under data/processed/."))
        added_text = "\n".join(item.text for item in patch.additions)
        merge_match = re.search(r"\.merge\([\s\S]{0,300}?left_index\s*=\s*True[\s\S]{0,300}?right_index\s*=\s*True", added_text)
        if merge_match:
            merge_line = next((item.number for item in patch.additions if ".merge(" in item.text), 0)
            findings.append(_finding(Severity.HIGH, "Dataset merge uses DataFrame index", patch, merge_line, "DATA_RULES.md", "External football datasets are merged by index.", "Rows can be matched to the wrong fixture.", "Normalize names and merge using documented match identifiers."))
        for added in patch.additions:
            text = added.text
            if re.search(r"(?:FTHG|FTAG|FTR|HTHG|HTAG|HTR).{0,80}\.fillna\(\s*0\s*\)", text, re.I):
                findings.append(_finding(Severity.HIGH, "Unplayed fixtures converted to zero", patch, added.number, "DATA_RULES.md", "A result/goals field is filled with zero.", "An incomplete fixture could enter analysis as a false 0-0 draw.", "Preserve missing values and exclude incomplete fixtures from result-based analysis."))
            if re.search(r"(?:api[_-]?key|token|password|secret)\s*=\s*[\"'][^\"']{8,}", text, re.I) and "os.environ" not in text:
                findings.append(_finding(Severity.CRITICAL, "Possible committed secret", patch, added.number, "PROJECT_RULES.md", "A credential-like literal was added.", "A secret could be exposed in Git history.", "Remove it, rotate it if genuine, and read secrets from environment variables."))
            if re.search(r"[A-Za-z]:\\\\|/(?:Users|home)/", text):
                findings.append(_finding(Severity.MEDIUM, "Machine-specific path", patch, added.number, "PROJECT_RULES.md", "An absolute machine path was added.", "The project will not be reproducible on another machine.", "Use pathlib and repository-relative paths."))
            if re.search(r"\b(causes?|proves?|leads to)\b", text, re.I) and patch.path.endswith((".py", ".ipynb", ".md")):
                findings.append(_finding(Severity.MEDIUM, "Potential causal claim", patch, added.number, "PROJECT_RULES.md", "A causal phrase was added.", "The project scope supports association, not causal inference.", "Use association or relationship unless a causal design is documented."))
            if re.search(r"\b(RandomForest|sklearn|tensorflow|django|flask|fastapi|sqlite|postgres)\b", text, re.I):
                findings.append(_finding(Severity.MEDIUM, "Potential scope creep", patch, added.number, "PROJECT_RULES.md", "Out-of-scope infrastructure or modelling appears in the diff.", "It may exceed the agreed academic project scope.", "Document approval or keep the change within the defined scope."))
    return findings
