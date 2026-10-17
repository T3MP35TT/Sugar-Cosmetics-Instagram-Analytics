# Implementation review

Reviewed: 2026-10-17

## Automated and reproducibility checks

- `python -m pytest -q --basetemp .pytest-temp-review-20261017-complete` — **52 passed in 20.56 seconds**, including model leakage/split checks and Streamlit smoke tests for the home page and all eight dashboard pages.
- `python -m compileall -q app.py pages src utils tests` — CI check configured; every page also executes in the automated Streamlit smoke suite.
- Category comparisons use a shared tested calculation for weighted rate, selected-scope reference, and percentage-point difference.
- GitHub Actions CI is configured to install supported dependencies, run the complete test suite, and compile project Python files on pushes and pull requests.
- `python src/run_model_evaluation.py` — **completed in about 15 seconds** on the local 50,000-row CSV; generated temporal evaluation and holdout prediction reports.
- The model uses only post type, campaign type, hashtag count, and calendar features. Reach, impressions, interaction counts, visits, follows, and potentially post-outcome labels are excluded from inputs.
- The split is chronological by unique dates; four expanding date-grouped CV folds use a seven-day gap. Fold-local preprocessing and a twelve-candidate Ridge/gradient-boosting grid prevent transform leakage and ad hoc tuning.
- The one-standard-error rule selected regularized Ridge (alpha 100) instead of the slightly lower-CV-error tree model.
- Temporal CV MAE was **0.062042** for the median baseline and **0.062199** for the selected ML candidate. On the untouched 9,980-record future holdout (2025-02-05 through 2025-04-19), baseline MAE was **0.062235** and ML-candidate MAE was **0.062265**; holdout R² was negative. The candidate loses to baseline at both stages, so model complexity is not justified and the recommended approach is the median baseline. The 95% date-block bootstrap interval for model-minus-baseline MAE was [-0.000015, 0.000072], crossing zero.
- Holdout errors are reported by month, post type, and campaign type. These are model error groups, not demographic fairness evidence.
- `MODEL_MONITORING_PLAN.md` records deployment gates, batch checks, review cadence, alert response, retraining criteria, and roles; it is a future-use plan, not an active service.
- Replaced deprecated Streamlit container-width arguments and made audit report source paths project-relative.
- `python src/reproducibility_manifest.py` — **completed**.
- Workbook and dashboard CSV — **50,000 rows and 14 columns match cell-by-cell** after normalizing headers, dates, numbers, and category whitespace.
- Reproducibility manifest reports 50,000 records over 366 calendar days (136.612 records per day). This is row density only; one row per post is unverified.
- The manifest quantifies post-type and campaign-type shares; their near-even counts are flagged as a sampling diagnostic, not proof of representativeness.
- Local version control — tracked on `main`; no remote or PR workflow is configured.

The first default `pytest` invocation could not create its temporary directory under the host's protected Temp path. The successful run used an isolated workspace temp directory. No application code change was needed for that environment restriction.

## Outstanding evidence gates

- The public upstream project is identified and rounded dataset aggregates match its README; the data collector, account identity, collection method, permission, row grain, and sampling method have not been independently confirmed.
- Whether the upstream license applies to the dataset itself requires review before redistribution.
- No external expected values are available for source metric reconciliation.
- The data contains no demographics, paid media, revenue, or attributed conversions; fairness and ROI cannot be assessed.
- No stakeholder-approved baseline, target, or experiment result exists.
- No remote, pull request, or second-person code review is available in this workspace.
- There is no verified prediction-time source workflow or later independent validation period, and the evaluated model does not beat the simple baseline.
- No production refresh feed or deployed model exists; recurring drift monitoring and retraining are not applicable to the current offline evaluation.

These are evidence gaps, not passing criteria. The offline model evaluation does not establish a useful deployable predictor.
