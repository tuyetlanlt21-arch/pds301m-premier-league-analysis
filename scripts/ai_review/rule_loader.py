"""Load review policy from canonical repository documentation."""

from pathlib import Path
import re


RULE_FILES = (
    "docs/PROJECT_RULES.md",
    "docs/DATA_RULES.md",
    "docs/DATA_CONTRACT.md",
    "docs/RESEARCH_QUESTIONS.md",
    "docs/ANALYSIS_PLAN.md",
)


def repository_root(start: Path | None = None) -> Path:
    """Find the root containing the canonical documentation directory."""
    current = (start or Path(__file__)).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "docs" / "PROJECT_RULES.md").is_file():
            return candidate
    raise FileNotFoundError("Could not locate repository review policy.")


def load_rules(root: Path | None = None) -> dict[str, str]:
    """Read canonical policy documents, failing clearly when one is absent."""
    base = root or repository_root()
    return {name: (base / name).read_text(encoding="utf-8") for name in RULE_FILES}


def contract_fields(rules: dict[str, str]) -> set[str]:
    """Extract documented raw-schema field names from the contract table."""
    contract = rules["docs/DATA_CONTRACT.md"]
    return set(re.findall(r"^\|\s*([A-Za-z][A-Za-z0-9_]*)\s*\|", contract, re.MULTILINE))
