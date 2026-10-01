# Automated AI Pull Request Review

## Purpose and advisory mode

The AI Review workflow adds project-specific advisory feedback to pull requests targeting `main`. It complements, and never replaces, the deterministic Quality Check. It is **not** a required branch-protection check and never auto-merges a pull request.

## Architecture

`scripts/ai_review/` separates unified-diff parsing, trusted policy loading, deterministic project-policy checks, optional provider calls, data models, and GitHub Markdown output. Policy is loaded from `PROJECT_RULES.md`, `DATA_RULES.md`, `DATA_CONTRACT.md`, `RESEARCH_QUESTIONS.md`, and `ANALYSIS_PLAN.md` rather than being an independent project specification.

## Review policy and severity

The deterministic layer flags raw-data mutation, result fields filled with zero, index-based data merges, credential-like literals, unsafe paths, causal language, and obvious scope creep. The optional provider is prompted with the canonical rules and PR diff to identify further issues including contract, research-question, architecture, scraping, traceability, and statistical-interpretation risks.

- **CRITICAL:** secrets, fabricated/corrupting data, or raw-data mutation.
- **HIGH:** false 0-0 fixtures, contract-breaking schema/merge risks, or materially wrong analysis.
- **MEDIUM:** research alignment, interpretation, validation, or responsibility concerns.
- **LOW:** maintainability and minor documentation concerns.

Any critical or high finding recommends `BLOCKED`; medium/low findings produce `PASS_WITH_COMMENTS`; no findings produces `PASS`. These are advisory recommendations only.

## Provider configuration

The provider is optional and configured only through GitHub configuration: `AI_REVIEW_API_KEY` (secret), plus `AI_REVIEW_PROVIDER`, `AI_REVIEW_MODEL`, and `AI_REVIEW_ENDPOINT` (repository variables). The adapter uses an OpenAI-compatible JSON endpoint but is not tied to a vendor. Missing configuration produces an explicit skipped/unavailable note, never a fabricated AI review.

Run locally without network or tokens:

```powershell
.venv\Scripts\python.exe -m scripts.ai_review.reviewer --diff-file path\to\change.diff --mock
```

## Workflow security

The workflow uses `pull_request_target` solely to run the trusted base-branch reviewer and update a PR comment. It checks out the base SHA, obtains the diff from GitHub's API, and never checks out or executes PR code. Fork PRs deliberately skip AI execution and receive a stable explanatory comment, so repository secrets are not exposed. A stable `<!-- pds301m-ai-review -->` marker ensures each PR has one updated bot comment rather than repeated comments.

## Promotion later

After observing advisory reviews on real PRs, add the AI Review status to main protection only if its false-positive rate and provider reliability are acceptable. Until then, only `validate` remains required.
