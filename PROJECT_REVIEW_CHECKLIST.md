# Project review scorecard and release gates

Use a 1–5 score only when the repository contains reviewable evidence. Mark a criterion **N/A** when it does not apply to this analytics project. Do not treat a written plan as completed evidence.

## Section ratings

Scores below rate the evidence currently in this repository, not whether the work is polished. A 5 requires evidence for every applicable criterion in that section.

| Section | Rating | Evidence supporting the rating | Main remaining gap |
|---|---:|---|---|
| 1. Data Foundations | **4/5** | Source project is identified; quality, EDA, category balance, missingness, duplicates, and outliers are documented; data-page caveats identify what could not be verified | Data collection, official account, row grain, sampling frame, and dataset-level license remain unconfirmed |
| 2. Methodology & Experimental Design | **5/5** | Business question is framed as descriptive association; prediction target and assumptions are explicit; median baseline, date-isolated holdout, four expanding date-grouped folds, and a seven-day gap are used; experiment planning states its assumptions | Owner approval is still required before using a business experiment or model operationally |
| 3. Modeling & Feature Engineering | **5/5** | Pre-publication features and leakage exclusions are documented; 27 configurations across five ML model families plus a median baseline are tuned systematically; overfit and future-holdout errors are examined; the simpler baseline is retained when the apparent ElasticNet gain is within uncertainty | No useful deployable ML predictor is demonstrated on this dataset |
| 4. Evaluation & Metrics | **4/5** | MAE, RMSE, R², temporal CV, future holdout, date-block uncertainty, monthly errors, and post-type/campaign subgroup errors are reported | Conditional inference depends on unverified sampling and date-block assumptions; demographic fairness cannot be assessed from absent demographic fields |
| 5. Code Quality & Reproducibility | **4/5** | Modular source, locked dependencies, seeds, hashes, reproducibility manifest, unit/smoke tests, and CI workflow are present | Full suite has not been rerun after the latest model-search changes; independent review and hosted CI result are unavailable |
| 6. Robustness & Limitations | **4/5** | Limitations and distribution-shift risks are stated; temporal validation and a deployment monitoring/retraining plan are documented | No verified recurring source, active monitoring, or expected production-volume benchmark exists |
| 7. Communication & Documentation | **4/5** | Dashboard pages provide KPIs, charts, takeaways, metric definitions, uncertainty caveats, and action-oriented documentation | Stakeholders have not reviewed or approved the final narrative and recommendations |
| 8. Business & Stakeholder Value | **4/5 for decision readiness** | The project answers the engagement question; a three-phase Marketing/Finance test portfolio now includes assumed owners, hypotheses, randomized designs, adjusted sample sizes, scenario economics, guardrails, and success/inconclusive/harm actions | A 5/5 requires named stakeholder approval, validated attribution and finance data, and observed randomized-test results showing incremental business impact; the scenario values are illustrative only |

## Current project evidence and remaining gate

| Area | Evidence present | Required before a defensible 5/5 |
|---|---|---|
| Data foundations | Public upstream project identified; local workbook metrics reconcile to its rounded README figures; quality and sampling checks are recorded | Confirm the upstream license covers the dataset and obtain collection method, account identity, row grain, and sampling details; reconcile source records independently |
| Methodology | Regression target, prediction-time feature contract, excluded post-outcome fields, chronological holdout, date-grouped expanding CV with a seven-day gap, experiment guidance, and a two-arm conversion-test sample-size approximation | Business owner must approve the outcome, baseline, minimum useful lift, test design, and decision threshold; account for clustering and attrition |
| Feature engineering | **5/5:** documented pre-publication format, campaign, format-by-campaign interaction, canonical hashtag-set, hashtag-count, and cyclical calendar features; fold-local imputation/encoding/scaling; explicit leakage exclusions and deterministic feature checks | Confirm every predictor is available in the actual publishing workflow before operational use; predictive value still requires verified future data |
| Modeling | **5/5 for modeling practice:** systematic 27-candidate comparison across baseline, regularized linear, histogram boosting, random forest, and extra trees models; one-standard-error selection; separate evaluation of the best ML candidate and selected baseline on the untouched future holdout; and rejection of complexity when any apparent gain is within uncertainty | This rates the rigor of model selection, not model utility. No useful deployable ML predictor is demonstrated; add verified prediction-time signal and validate on a later independent period before using ML operationally |
| Evaluation | Temporal CV, untouched future holdout, MAE/RMSE/R², date-block model interval, train-validation gap, monthly residuals and post-type/campaign subgroup errors; descriptive category contrasts include simultaneous 95% date-block intervals and an observed gap equivalent at category reach | Do not interpret conditional intervals as population significance or the gap equivalent as incremental impact; repeat on verified, independently collected future data and validate date-block assumptions |
| Code quality | Modular calculations, locked environment, 88 passing tests, automated smoke checks for every page, model leakage/split tests, statistical inference, business-attribution validation/calculation, and experiment-calculator tests, plus GitHub Actions CI configuration | Independent code review and execution of CI in the hosted repository |
| Robustness | Empty/invalid input handling, chronological validation, unseen-category-tolerant encoding, cached reload keyed to file modification and size, quality checks, automated app smoke tests, and [a monitoring/retraining plan](MODEL_MONITORING_PLAN.md) | Exercise a real recurring refresh source and agree drift/alert thresholds before production deployment |
| Scalability | Expanded model evaluation completed on the 50,000-row input in about 156 seconds on the local environment | Production volume and hardware are unknown; benchmark at expected scale before deployment |
| Communication | Executive dashboard, metric definitions, plain-language caveats, downloadable filtered contrast tables with uncertainty, and an actionable Marketing/Finance experiment portfolio documented in the dashboard | Stakeholder review confirms the narrative is understood and current |
| Business value | Descriptive performance measures, uncertainty-aware format/campaign contrasts, quantified observed gap equivalents, a sequenced test portfolio with sample-size and assumption-based economics, and an upload workflow for attributed conversions, revenue, variable cost, paid spend, ROI, and randomized-arm outcomes | No genuine attribution export was supplied, so observed financial or incremental impact remains unmeasured. The observed gap equivalent and scenario values are not incremental results. Reconcile a real source export under the [business-impact data contract](BUSINESS_IMPACT_DATA_CONTRACT.md) before reporting impact |

## Criterion applicability

The project includes an offline predictive regression evaluation in addition to descriptive reporting. Train/test separation, temporal cross-validation, model comparison, tuning, overfit diagnostics, and error analysis are implemented. The strongest ML candidate's holdout MAE is fractionally lower than the median baseline, but the difference is negligible and the date-block interval includes zero; no useful advantage is established. Retraining and production model monitoring remain N/A until an approved data feed and deployed model exist.

Demographic fairness, time-of-day analysis, and ROI cannot be assessed with the supplied fields. Model subgroup errors are reported by post type and campaign type. Predictive-model performance remains conditional on this file because its collection process and row grain are unverified. Missing source and business evidence must come from the data owner or stakeholders; code changes cannot manufacture it.

## Reproducible review procedure

1. Create the environment from `requirements-lock.txt` and record the Python version.
2. Run `python src/reproducibility_manifest.py` to fingerprint source files, project code, tests, notebook, lock file, and runtime. Confirm `input_consistency.status` is `match`; the manifest hash identifies exact bytes but does not prove authenticity.
3. Run the notebook top to bottom and review the exported quality flags and outlier file.
4. Run `pytest -q` and record the command and result in the review record. If the default temporary directory is inaccessible, use a fresh workspace directory with `pytest -q --basetemp .pytest-temp-review`. CI runs unit tests, all-page smoke tests, and Python compilation.
5. Have the data owner reconcile a sample of source metrics and confirm provenance and row grain.
6. Have the business owner approve the primary outcome, experiment decision rule, and impact measure.

Record each result, reviewer, and date in the release review. Keep unverified gates open.
