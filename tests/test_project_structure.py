from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_day_one_required_files_exist() -> None:
    required = [
        "README.md", "requirements.txt", "main.py", "notebooks/premier_league_analysis.ipynb",
        "docs/PROJECT_RULES.md", "docs/DATA_CONTRACT.md", "docs/RESEARCH_QUESTIONS.md",
        "scripts/validate_project.py", ".github/workflows/quality-check.yml",
    ]
    assert all((ROOT / item).is_file() for item in required)
