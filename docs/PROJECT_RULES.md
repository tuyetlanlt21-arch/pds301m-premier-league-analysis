# Project Rules

1. **Raw data is immutable.** `data/raw/` contains externally collected data and is never manually altered; transformations create new `data/processed/` outputs.
2. **Never fabricate data.** Never invent real-looking matches, scores, teams, statistics, or findings. Synthetic values are permitted only in clearly identified tests or educational examples.
3. **Separate responsibilities.** `data_collection.py` collects external data; `processor.py` validates, cleans, normalizes, and engineers features; `analysis.py` contains NumPy/Pandas analysis; `basics.py` covers Python basics; `data_structures.py` covers list/dict/set/tuple; `main.py` orchestrates.
4. **Research questions drive analysis.** Major analyses and visualizations must support a defined question.
5. **No hard-coded findings.** Conclusions require collected and analyzed data.
6. **Association is not causation.** Use association, relationship, or pattern unless causal analysis is performed.
7. **Unplayed matches are not draws.** Never fill missing results/goals to make a fake 0–0.
8. **Reproducibility.** Use `pathlib` and repository-relative paths; never use machine-specific paths.
9. **Source traceability.** Preserve season, source, and collection method; do not silently mix sources.
10. **Validate before analysis.** Validate data before analytical conclusions.
11. **Safe multi-source integration.** Never merge by DataFrame index; normalize team names and use Season/Date/HomeTeam/AwayTeam as a potential key.
12. **Notebook responsibility.** The notebook is the narrative; reusable code belongs in `src/` and the notebook combines code, tables, visualizations, and Markdown interpretation.
13. **Keep scope.** Do not add ML, prediction, databases, backend/frontend apps, or dashboards without later approval.
14. **Explicit contract changes.** If a source lacks a required field, document the limitation, affected questions, and alternatives; wait for approval before changing `DATA_CONTRACT.md`.
15. **Do not work ahead.** Respect day-specific progression.

## Git workflow

`main` is the protected, stable branch. All work follows: `main → feature/chore branch → commit → push → Pull Request → CI → review → merge`. Never work directly on `main`. Recommended prefixes: `feat/`, `fix/`, `chore/`, `docs/`, and `test/`.
