# Final Integration & Submission QA

**Status:** The code and documentation checks below pass. Final submission sign-off is pending because this QA workspace has no collected season CSVs and no native Jupyter/IPython runtime for a fresh Run All against the team's data.

## QA results

| Check | Result | Evidence |
|---|---|---|
| Dependencies and setup instructions | PASS | Added the missing `requirements.txt`; README installation commands now point to existing dependency files. Updated T13/T14 setup guidance. |
| Unit tests | PASS | `py -m unittest discover -s tests -v` — 8 tests passed, covering saved-CSV loading, season inference, cleaning, feature engineering, chart generation, insights, and report rendering. |
| Python imports and syntax | PASS | `python -m compileall -q src scripts tests` completed successfully. |
| Notebook structure | PASS | Notebook JSON parses; all 15 code cells compile. |
| Collection-to-report integration | PASS with temporary test fixtures | Both CLI scripts loaded CSVs from `data/raw/`, retained 6 completed test matches, generated all 8 charts and `charts/insights.md`, and generated `report/final_report.md`. Test fixtures were created in a temporary directory and removed; they are not project data. |
| Raw-data preservation | PASS with temporary test fixtures | SHA-256 hashes of the temporary input CSVs were unchanged after processing and report generation. |
| T13 chart preservation | PASS with temporary test fixtures | SHA-256 hashes of all 8 T13 chart files were unchanged after running the T15 report command. |
| Secrets and machine-specific paths | PASS | Static scan of project source, notebook, README files, and dependency files found no credentials or machine-specific absolute paths. |
| Fresh native Jupyter Run All on team data | NOT VERIFIED HERE | No CSV files are present in `data/raw/`; this QA runtime also has no IPython/nbclient. The user previously ran the notebook successfully in VS Code, but that does not replace the requested final fresh run. |
| Git/PR readiness | NOT VERIFIED HERE | This workspace is a merged source folder without a Git checkout, so repository status, branch integration, and PR checks cannot be inspected here. |

The analysis code reads saved CSV snapshots and does not download or alter raw data. Descriptive findings apply only to the seasons supplied by the team. Missing optional statistics remain missing. No findings have been hard-coded into the report generator.

## Final checks needed in the team's repository

1. Merge the files from the T16 package into the existing repository, keeping the team's real `data/raw/` CSVs.
2. From the repository root, install dependencies in the selected Windows Python environment:

   ```powershell
   py -m pip install -r requirements.txt
   py -m pip install -r requirements-t14.txt
   ```

3. Run the tests:

   ```powershell
   py -m unittest discover -s tests -v
   ```

4. Open `notebooks/premier_league_analysis.ipynb` in VS Code, select that same Python environment, choose **Restart Kernel → Run All**, and save the notebook after it completes.
5. Run `py -m scripts.generate_final_report`, then confirm `report/final_report.md` agrees with the notebook findings and limitations.
6. Review the merged diff and have all team members participate in the final review. Fill the contribution table in README with the real work completed before submission.

Do not mark the PR ready until these local-data, notebook, report-review, and team-review checks pass. No commit or PR was created in this QA workspace.

## Team review confirmations

| Student ID | Team member | Review / run confirmation |
|---|---|---|
| SE203600 | Lê Thị Tuyết Lan |  |
| SE180021 | Nguyễn Hoàng Thùy Linh |  |
| SE203216 | Trần Long Vân |  |
| SE190537 | Nguyễn Quốc Toàn |  |
