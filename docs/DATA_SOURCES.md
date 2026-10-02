# Data Sources

## Football-Data: match-level source

- **Role:** Primary source for EPL match results and match statistics.
- **Format:** CSV; no API key is required.
- **Example:** [2025/26 EPL CSV](https://www.football-data.co.uk/mmz4281/2526/E0.csv).
- **Season pattern:** `https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv` (for example, `2324`, `2425`, `2526`).
- **Audit performed:** 2026-10-02. Each target CSV returned HTTP 200 and contained 380 rows; all 380 rows had completed-match scores. All checked match fields were present in each header, with no blank values among completed rows.
- **Target seasons checked:** `2324` (2023/24), `2425` (2024/25), and `2526` (2025/26).
- **Usage note:** The provider states the data is intended for private individuals and excludes commercial use and data-training products involving automated bots/scrapers/AI. Recheck its current terms before collection or redistribution; do not treat this project as permission to republish the source data.

### Source-to-contract mapping

| Canonical field(s) | Football-Data CSV mapping | Verification/status |
| --- | --- | --- |
| `Season` | Assign from the requested season code; it is not a CSV column. | Verified mapping rule for all three URLs. |
| `Date`, `HomeTeam`, `AwayTeam` | Same-named CSV columns. | Present in each target-season CSV. Parse `Date` as day-first. |
| `FTHG`, `FTAG`, `FTR` | Same-named CSV columns. | Present and nonblank for all 380 completed rows in each target season. |
| `HTHG`, `HTAG`, `HTR` | Same-named CSV columns. | Present and nonblank for all 380 completed rows in each target season. |
| `HS`, `AS`, `HST`, `AST` | Same-named CSV columns. | Shots and shots on target present and nonblank for all 380 completed rows in each target season. |
| `HC`, `AC` | Same-named CSV columns. | Corners present and nonblank for all 380 completed rows in each target season. |
| `HY`, `AY`, `HR`, `AR` | Same-named CSV columns. | Yellow and red cards present and nonblank for all 380 completed rows in each target season. |
| `source`, `collection_method`, `source_url`, `retrieved_at` | Add as project provenance metadata during collection; do not infer these from match fields. | Required for traceability; not supplied as match columns. |

### FBref: sample match-report inspection

The automated page-inspection tool returned HTTP 403 on 2026-10-02, but browser screenshots supplied on 2026-10-03 confirm that the user can open FBref's 2023-2024 Premier League Scores & Fixtures page and a Match Report. The fixture table visibly includes date, home team, score, away team, attendance, venue, referee, and a Match Report link.

The supplied Match Report is Burnley vs. Manchester City, 11 August 2023. Its visible content verifies, for this single match only:

| Contract/statistic | Evidence in the supplied screenshot | Status |
| --- | --- | --- |
| `Date`, teams, full-time score | Match heading and displayed 0-3 score; the fixture table also has date/team/score columns. | Observed for the sample match. `FTR` can be derived from the score. |
| Half-time score/result | Timeline shows goals at 4' and 36' before the Half Time marker. | 0-2 and the corresponding result can be inferred for this match; no explicit half-time score column is visible in the screenshot. |
| `HS`, `AS`, `HST`, `AST` | Team Stats shows “1 of 6” and “8 of 17” under Shots on Target. | Appears to report shots on target out of total shots for this match; verify labels/values against the page before transcribing. |
| `HC`, `AC` | Team Stats shows corners 6 and 5. | Observed for the sample match. |
| Cards | Timeline shows a red-card event at 90+4'; a Cards section is visible. | A red-card event is observed; season-wide card columns and per-team yellow/red counts are not verified from these screenshots. |

This is a one-match visual inspection, not a season-wide completeness audit or a downloadable dataset validation. Therefore FBref is a supplementary manual cross-check only; Football-Data remains the primary source for the three-season analysis because its CSV headers and rows were checked across all target seasons. The earlier HTTP 403 describes the automated inspection tool, not a general inability to access FBref in a browser.

### Research-question impact

No planned research question needs to be dropped for missing match fields in the three audited Football-Data seasons: RQ1 uses `FTR`; RQ2 uses goals, shots, and shots on target; RQ3 uses half-time and full-time results; RQ4 uses full-time goals; and RQ5 uses shots, shots on target, corners, and optional cards. The FBref screenshots provide a one-match cross-check for some of these statistics, but do not establish season-wide availability. This availability check does not establish source accuracy or validate duplicates/team naming; those are data-quality checks for later tasks. Wikipedia is season-level context only and does not supply fields for these match-level questions.

## Wikipedia: season-level context

- **Role:** Supplementary scrape of season-level context from [List of Premier League seasons](https://en.wikipedia.org/wiki/List_of_Premier_League_seasons).
- **Not a substitute for:** Football-Data match results or match statistics.
- Record the page URL and retrieval date, inspect the actual season table before parsing, and attribute reused content under Wikipedia's applicable license. Do not silently join season-level facts into match records.

## Initial scope and collection checks

The initial target is 2023/24, 2024/25, and 2025/26, verified in Football-Data's season index and direct CSV responses on 2026-10-02. Keep each downloaded source file immutable under `data/raw/`; record source URL, season, and retrieval date. Before implementing repeat collection, check applicable terms/policies, relevant robots restrictions, request rate, and CSV encoding/header. Include only completed matches in result-based analysis and never fill missing results with 0–0.

## Collection methodology

The collector uses Python `requests` to retrieve one verified season CSV with a 20-second timeout and a descriptive user-agent. Request start times are spaced at least one second apart, including after a failed request. It validates the supported season and required headers, preserves source strings and incomplete fixtures, and adds season, source, collection method, source URL, and UTC retrieval time to every row. It writes one CSV per season under `data/raw/` using exclusive file creation, so an existing raw file is never overwritten. The audit reports incomplete results, duplicate match keys, and blank cells without changing or dropping source records.

Run `python scripts/collect_data.py` to collect all three verified seasons, or pass `--seasons 2025/26` to collect one. The script writes one provenance-bearing CSV per season and refuses to overwrite an existing raw file. Its audit output reports incomplete fixtures, duplicate match keys, and blank values; investigate these in later validation/cleaning rather than altering the raw source.

Collection run on 2026-10-02 produced `data/raw/epl_2324_raw.csv`, `data/raw/epl_2425_raw.csv`, and `data/raw/epl_2526_raw.csv` (380 rows each). The audit found zero incomplete fixtures and zero duplicate match keys in each file. Blank cells were present in some bookmaker odds columns, but none of the canonical match-analysis fields were blank; odds are outside this project's research questions and must not be imputed into the analysis.

## Source limitations

- Football-Data warns that it cannot guarantee accuracy in its compiled data. Preserve the source files and validate results, team names, duplicates, and missing values before analysis.
- Some bookmaker odds fields are blank in the downloaded seasons. Odds are outside the defined research questions and are not imputed or analyzed.
- FBref was accessible in the user's browser but returned HTTP 403 to the automated inspection tool. Screenshots confirm one 2023/24 match report only; completeness across matches/seasons and exportability remain unverified.
- Wikipedia is used only for season-level context. It does not replace match-level data; any reused content must be attributed under the applicable license.
- Recheck Football-Data terms before redistribution or any use outside this individual coursework. The provider states the data is intended for private individuals and excludes commercial use and data-training products involving automated bots/scrapers/AI.
