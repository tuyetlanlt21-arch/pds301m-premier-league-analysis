# Premier League Match Analysis

## Project Overview

PDS301M project scaffold for studying Premier League match outcomes and match statistics using reproducible Python workflows.

## Main Research Question

How are home advantage, goals, and match statistics associated with win/draw/loss outcomes in the Premier League?

## Research Questions

RQ1 home advantage; RQ2 team attacking performance; RQ3 half-time versus full-time outcomes; RQ4 goal distribution; and RQ5 match-statistic associations. See [research questions](docs/RESEARCH_QUESTIONS.md).

## Planned Data Sources

Football-Data's EPL `E0.csv` files are the primary source for match-level results and statistics; they can be downloaded as CSV without an API key. FBref is a supplementary match-report source for manual cross-checks; only one 2023/24 match report has been inspected so far. Wikipedia's list of Premier League seasons is a supplementary source for season-level context, not match statistics. The initial target seasons are 2023/24, 2024/25, and 2025/26. See [data sources](docs/DATA_SOURCES.md) for URLs, source roles, and limitations.

## Planned Data Pipeline

Web Sources → Data Collection → Raw Dataset → Validation → Cleaning → Normalization → Feature Engineering → NumPy Analysis → Pandas Analysis → Visualization → Processed Outputs → Insights → Mini Report

## Project Structure

- `data/raw/`: immutable externally collected data
- `data/processed/`: derived outputs
- `src/`: reusable project code
- `notebooks/`: analytical narrative
- `docs/`: scope, rules, questions, contract, and plans
- `scripts/validate_project.py`: Day 1 structural validator

## Technologies

Python, Pandas, NumPy, Matplotlib, Seaborn, Requests, Beautiful Soup, Jupyter, and pytest.

## Development Workflow

`main` is stable. Use `main → feature/chore branch → commit → push → Pull Request → CI → review → merge`; do not work directly on main. Recommended prefixes are `feat/`, `fix/`, `chore/`, `docs/`, and `test/`.

## Current Status

**Raw data collected.** Three verified Football-Data EPL CSVs are stored under `data/raw/`. The collector, source audit, and offline quality tests are implemented. Cleaning, analysis, charts, and the report remain to be completed.
