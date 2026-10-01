# Premier League Match Analysis

## Project Overview

PDS301M project scaffold for studying Premier League match outcomes and match statistics using reproducible Python workflows.

## Main Research Question

How are home advantage, goals, and match statistics associated with win/draw/loss outcomes in the Premier League?

## Research Questions

RQ1 home advantage; RQ2 team attacking performance; RQ3 half-time versus full-time outcomes; RQ4 goal distribution; and RQ5 match-statistic associations. See [research questions](docs/RESEARCH_QUESTIONS.md).

## Planned Data Sources

Web scraping is the planned collection method. FBref is the candidate primary source and Football-Data is supplementary/reference. Sources will be inspected in Day 2 before collection.

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

**Day 1 – Project setup and data design.** No real data has been collected, scraped, cleaned, analyzed, or visualized.
