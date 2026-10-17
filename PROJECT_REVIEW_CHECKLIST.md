# Project review scorecard and release gates

Use a 1–5 score only when the repository contains reviewable evidence. Mark a criterion **N/A** when it does not apply to this descriptive dashboard. Do not treat a written plan as completed evidence.

## Current project evidence and remaining gate

| Area | Evidence present | Required before a defensible 5/5 |
|---|---|---|
| Data foundations | Public upstream project identified; local workbook metrics reconcile to its rounded README figures; quality and sampling checks are recorded | Confirm the upstream license covers the dataset and obtain collection method, account identity, row grain, and sampling details; reconcile source records independently |
| Methodology | Metric definitions, denominators, association caveats, and experiment guidance | Stakeholders approve the business outcome, comparison design, and decision threshold |
| Feature engineering | Shared calculations; explicit missing and zero-denominator handling | Independent hand-calculated source examples are reconciled and recorded |
| Evaluation | Category comparisons and outlier screening | Relevant baselines and uncertainty/sensitivity analysis are supplied; experiment results support causal claims |
| Code quality | Modular calculations, setup instructions, calculation tests, and pinned environment snapshot | Tests run in the documented environment; code review and Git history are available |
| Robustness | Empty selections and data checks are handled in the app; outliers are review-only | Critical-path edge cases and refresh failures are exercised and documented |
| Communication | Executive dashboard, metric definitions, limitations, and recommendations | Stakeholder review confirms the narrative is understood and current |
| Business value | Experiment framework and next-data list | Validated conversion/revenue linkage quantifies impact; owners approve a target and next action |

## Criterion applicability

The project is descriptive. Train/validation/test splits, cross-validation, model choice, hyperparameter tuning, model fit, model complexity, and predictive model monitoring are **N/A** until a predictive model is introduced. They must not be scored as completed.

Fairness across demographics, time-of-day analysis, ROI, and drift under production use cannot be assessed with the supplied fields. Predictive model criteria also remain N/A until a prediction target and valid prediction-time features are approved. Missing source and business evidence must come from the data owner or stakeholders; code changes cannot manufacture it.

## Reproducible review procedure

1. Create the environment from `requirements-lock.txt` and record the Python version.
2. Run `python src/reproducibility_manifest.py` to fingerprint source files, project code, tests, notebook, lock file, and runtime. Confirm `input_consistency.status` is `match`; the manifest hash identifies exact bytes but does not prove authenticity.
3. Run the notebook top to bottom and review the exported quality flags and outlier file.
4. Run `pytest -q` and record the command and result in the review record. If the default temporary directory is inaccessible, use a fresh workspace directory with `pytest -q --basetemp .pytest-temp-review`.
5. Have the data owner reconcile a sample of source metrics and confirm provenance and row grain.
6. Have the business owner approve the primary outcome, experiment decision rule, and impact measure.

Record each result, reviewer, and date in the release review. Keep unverified gates open.
