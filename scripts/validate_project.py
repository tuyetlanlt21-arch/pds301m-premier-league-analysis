"""Validate Day 1 repository structure only; it does not validate football data."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRECTORIES = ("data/raw", "data/processed", "src", "notebooks", "charts", "report", "docs", "tests", "scripts", ".github/workflows")
REQUIRED_FILES = (
    "main.py", "requirements.txt", "README.md", "data/raw/.gitkeep", "data/processed/.gitkeep", "charts/.gitkeep", "report/.gitkeep",
    "src/__init__.py", "src/basics.py", "src/data_structures.py", "src/data_collection.py", "src/processor.py", "src/analysis.py",
    "notebooks/premier_league_analysis.ipynb", "tests/__init__.py", "docs/PROJECT_SCOPE.md", "docs/RESEARCH_QUESTIONS.md",
    "docs/DATA_CONTRACT.md", "docs/DATA_SOURCES.md", "docs/DATA_RULES.md", "docs/ANALYSIS_PLAN.md", "docs/PROJECT_RULES.md",
    ".github/pull_request_template.md", ".github/workflows/quality-check.yml",
)


def main() -> int:
    """Report absent structural requirements and return a suitable exit code."""
    missing = [item for item in REQUIRED_DIRECTORIES if not (ROOT / item).is_dir()]
    missing += [item for item in REQUIRED_FILES if not (ROOT / item).is_file()]
    if missing:
        print("Day 1 project validation failed. Missing:")
        print("\n".join(f"- {item}" for item in missing))
        return 1
    print("Day 1 project structure validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
