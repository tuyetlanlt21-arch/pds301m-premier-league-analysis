# Premier League Match Analysis (P6)

A PDS301M project describing Premier League match outcomes, team attacking performance, half-time to full-time results, goal distributions, and match-statistic relationships. The analysis covers the season CSV files placed in `data/raw/`; it does not assume a fixed season range or hard-code findings.

## Research questions

1. Do home wins occur more often than draws or away wins in the included matches?
2. Which teams scored and shot the most, in total and per appearance?
3. How are half-time outcomes associated with full-time outcomes?
4. How are total goals distributed across matches and seasons?
5. How do available match-statistic totals vary by result and correlate with one another?

The project answers these descriptively. It does not make causal claims or present half-time results as a validated prediction model.

## Data sources and input

- [Football-Data.co.uk England match data](https://www.football-data.co.uk/englandm.php) is the source for match-level CSV files.
- [List of Premier League seasons](https://en.wikipedia.org/wiki/List_of_Premier_League_seasons) is optional season context, not match-level input.

Save one or more downloaded season CSVs in `data/raw/`, for example `epl_2324_raw.csv`. The filename should contain a four-digit season code such as `2324`, unless the file already has a `Season` column. Required fields are `Date`, `HomeTeam`, `AwayTeam`, `FTHG`, and `FTAG`. Half-time scores and match-statistic fields are optional. Missing optional statistics remain missing; they are not treated as zero. The notebook and scripts work from saved files and do not fetch data from the internet.

## Reproduce the analysis (Windows)

Open the repository root in VS Code. In **Terminal → New Terminal**, run:

```powershell
py -m pip install -r requirements.txt
py -m pip install -r requirements-t14.txt
```

In VS Code, open `notebooks/premier_league_analysis.ipynb`, select the Python environment where these packages were installed, then choose **Restart Kernel → Run All**. The notebook creates or refreshes the figures in `charts/` and the insights file `charts/insights.md`.

To run the visualizations and create the T15 report from the command line instead:

```powershell
py -m scripts.generate_final_report
```

This command cleans the current CSV files, calculates report findings in a temporary folder, and writes `report/final_report.md`. It leaves the existing T13 PNGs and `charts/insights.md` unchanged. Run the notebook or `py -m scripts.generate_visualizations` separately when you want to refresh T13 charts.

Run the project quality checks with:

```powershell
py -m unittest discover -s tests -v
```

## Project structure

```text
.
├── data/raw/                         # Saved Football-Data season CSVs
├── notebooks/premier_league_analysis.ipynb  # Full T14 analysis narrative
├── src/
│   ├── analysis.py                   # Reusable chart functions
│   ├── data_pipeline.py              # CSV loading, checks, cleaning, features
│   └── reporting.py                  # Data-backed T15 report renderer
├── scripts/
│   ├── generate_visualizations.py    # Chart and T13 insights generation
│   └── generate_final_report.py      # Charts + T15 report command
├── charts/                           # Generated PNGs and insights.md
├── report/final_report.md            # Generated mini report
├── tests/                             # Visualization, pipeline, and report tests
├── requirements.txt                   # Existing project dependencies
└── requirements-t14.txt               # Notebook and visualization dependencies
```

## Method and limitations

The pipeline loads the local CSVs, parses dates and numeric fields, retains completed matches with valid full-time scores, removes duplicate match keys, and derives outcome and combined-statistic features. Pandas and NumPy produce grouped summaries; Matplotlib and Seaborn render the figures. The input may omit optional odds or match statistics, so some comparisons or plots may be unavailable. Results cover only the seasons present in the local files, team totals depend on appearances, and Pearson correlation indicates association rather than cause.

## Team contributions

Complete this table with the real team member names and work performed; do not leave role placeholders in the submitted README.

| Student ID | Member | Contribution |
|---|---|---|
| SE203600 | Lê Thị Tuyết Lan |  |
| SE180021 | Nguyễn Hoàng Thùy Linh |  |
| SE203216 | Trần Long Vân |  |
| SE190537 | Nguyễn Quốc Toàn |  |
