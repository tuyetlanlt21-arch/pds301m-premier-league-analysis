# Final Analysis Notebook

Notebook: `notebooks/premier_league_analysis.ipynb`

The notebook follows the P6 analysis story: Introduction, RQs, Sources, Basics, Data Structures, Collection, Understanding, Cleaning, Features, NumPy, Pandas RQ1–RQ5, Visualization, Findings, Limitations, and Conclusion. Reusable CSV loading, cleaning, feature engineering, and chart logic is kept in `src/` and `scripts/`.

## Files in the package

- `notebooks/premier_league_analysis.ipynb` — complete analysis notebook.
- `src/data_pipeline.py` — reusable offline CSV loading, data checks, cleaning, features, and basic/data-structure helpers.
- `src/analysis.py` — reusable T13 chart functions, with an informative scatter placeholder when optional shot data is unavailable.
- `scripts/generate_visualizations.py` — chart insight report writer used by the notebook.
- `tests/test_analysis_visualizations.py` — T13 chart tests.

## Apply the package

Extract the package into the project root and merge folders. Replace the existing notebook, `src/analysis.py`, and `scripts/generate_visualizations.py`; add `src/data_pipeline.py`. Keep the season CSVs in `data/raw/` (for example, `epl_2324_raw.csv`). The notebook does not download or alter raw files.

## Run the notebook

1. From the repository root, install `py -m pip install -r requirements.txt` and `py -m pip install -r requirements-t14.txt`. Install the VS Code Jupyter extension if needed.
2. Open the repository folder in VS Code and open `notebooks/premier_league_analysis.ipynb`.
3. Select the project's Python environment as the notebook kernel.
4. Select **Restart Kernel → Run All**.

The notebook writes eight PNG charts and `charts/insights.md`. Missing optional statistics remain missing; charts that need unavailable shot totals explain the data limitation instead of reporting zero shots. Run All requires at least one season CSV in `data/raw/` with the core Football-Data columns `Date`, `HomeTeam`, `AwayTeam`, `FTHG`, and `FTAG`.
