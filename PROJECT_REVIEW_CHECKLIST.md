# Project review scorecard and release gates

Use a 1–5 score only when the repository contains reviewable evidence. Mark a criterion **N/A** when it does not apply to this analytics project. Do not treat a written plan as completed evidence.

## Current project evidence and remaining gate

| Area | Evidence present | Required before a defensible 5/5 |
|---|---|---|
| Data foundations | Public upstream project identified; local workbook metrics reconcile to its rounded README figures; quality and sampling checks are recorded | Confirm the upstream license covers the dataset and obtain collection method, account identity, row grain, and sampling details; reconcile source records independently |
| Methodology | Regression target, prediction-time feature contract, excluded post-outcome fields, chronological holdout, date-grouped expanding CV with a seven-day gap, and experiment guidance | Business owner must approve the prediction use and decision threshold before operational use |
| Feature engineering | Pre-publication category/date/hashtag-count features, fold-local imputation/encoding/scaling, missing/zero-denominator handling, and leakage tests | Feature definitions still require confirmation against the actual publishing workflow |
| Modeling | Median baseline, Ridge and histogram-gradient candidates, 12-point grid, one-standard-error simplicity rule; model rejected for deployment when baseline wins | Holdout shows no performance gain over baseline; additional valid predictors and a later independent period are needed before a useful model can be justified |
| Evaluation | Temporal CV, untouched future holdout, MAE/RMSE/R², date-block bootstrap interval, train-validation gap, monthly residuals and post-type/campaign subgroup errors | Do not interpret the conditional interval as population significance; repeat on verified, independently collected future data |
| Code quality | Modular calculations, locked environment, 52 passing tests, automated smoke checks for every page, model leakage/split tests, and GitHub Actions CI configuration | Independent code review and execution of CI in the hosted repository |
| Robustness | Empty/invalid input handling, chronological validation, unseen-category-tolerant encoding, cached reload keyed to file modification and size, quality checks, automated app smoke tests, and [a monitoring/retraining plan](MODEL_MONITORING_PLAN.md) | Exercise a real recurring refresh source and agree drift/alert thresholds before production deployment |
| Scalability | Full model evaluation completed on the 50,000-row input in about 13 seconds on the local environment | Production volume and hardware are unknown; benchmark at expected scale before deployment |
| Communication | Executive dashboard, metric definitions, plain-language caveats, and action-oriented experiment recommendations | Stakeholder review confirms the narrative is understood and current |
| Business value | Descriptive performance measures and an experiment brief with outcomes, guardrails, stopping rule, and next-data requirements | Validated conversion/revenue linkage quantifies impact; owners approve a target and next action |

## Criterion applicability

The project includes an offline predictive regression evaluation in addition to descriptive reporting. Train/test separation, temporal cross-validation, model comparison, tuning, overfit diagnostics, and error analysis are implemented. The model is not cleared for production because it does not outperform the median baseline on the untouched holdout. Retraining and production model monitoring remain N/A until an approved data feed and deployed model exist.

Demographic fairness, time-of-day analysis, and ROI cannot be assessed with the supplied fields. Model subgroup errors are reported by post type and campaign type. Predictive-model performance remains conditional on this file because its collection process and row grain are unverified. Missing source and business evidence must come from the data owner or stakeholders; code changes cannot manufacture it.

## Reproducible review procedure

1. Create the environment from `requirements-lock.txt` and record the Python version.
2. Run `python src/reproducibility_manifest.py` to fingerprint source files, project code, tests, notebook, lock file, and runtime. Confirm `input_consistency.status` is `match`; the manifest hash identifies exact bytes but does not prove authenticity.
3. Run the notebook top to bottom and review the exported quality flags and outlier file.
4. Run `pytest -q` and record the command and result in the review record. If the default temporary directory is inaccessible, use a fresh workspace directory with `pytest -q --basetemp .pytest-temp-review`. CI runs unit tests, all-page smoke tests, and Python compilation.
5. Have the data owner reconcile a sample of source metrics and confirm provenance and row grain.
6. Have the business owner approve the primary outcome, experiment decision rule, and impact measure.

Record each result, reviewer, and date in the release review. Keep unverified gates open.
