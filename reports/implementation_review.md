# Implementation review

Reviewed: 2026-10-17

## Automated and reproducibility checks

- `python -m pytest -q --basetemp .pytest-temp-review-20261017-impact` — **88 passed in 18.69 seconds** before the latest model-report refinement; the model evaluation was rerun after that refinement, but the full test suite was not rerun.
- `python -m compileall -q app.py pages src utils tests` — passed; CI repeats this check, and every page also executes in the automated Streamlit smoke suite.
- Category comparisons use a shared tested calculation for weighted rate, selected-scope reference, and percentage-point difference.
- GitHub Actions CI is configured to install supported dependencies, run the complete test suite, and compile project Python files on pushes and pull requests.
- `python src/run_model_evaluation.py` — regenerated the temporal evaluation and holdout predictions after separating the one-SE selected approach from the strongest ML candidate.
- The model uses pre-publication post type, campaign, their interaction, canonical hashtag set/count, and calendar features. Reach, impressions, interaction counts, visits, follows, and potentially post-outcome labels are excluded from inputs.
- The split is chronological by unique dates; four expanding date-grouped CV folds use a seven-day gap. Fold-local preprocessing and a systematic 27-candidate search cover the median baseline, Ridge, ElasticNet, histogram gradient boosting, random forest, and extra trees.
- The one-standard-error rule uses fold standard error (fold MAE standard deviation divided by the square root of four) and selects the median baseline. ElasticNet (alpha 0.01, L1 ratio 0.25) is the lowest-MAE ML candidate in temporal CV and is separately evaluated on the future holdout.
- Temporal CV MAE was **0.062042** for the median baseline and **0.062040** for ElasticNet. On the untouched 9,980-record future holdout (2025-02-05 through 2025-04-19), baseline MAE was **0.06223522** and ElasticNet MAE was **0.06223515** (R² **-0.000023**). The holdout point difference is negligible; its date-block 95% interval for ML-minus-baseline MAE was **[-0.00000734, 0.00000724]**, crossing zero. Model complexity is not justified. The one-SE selection and deployment recommendation remain the median baseline.
- Holdout errors are reported by month, post type, and campaign type. These are model error groups, not demographic fairness evidence.
- `MODEL_MONITORING_PLAN.md` records deployment gates, batch checks, review cadence, alert response, retraining criteria, and roles; it is a future-use plan, not an active service.
- Replaced deprecated Streamlit container-width arguments and made audit report source paths project-relative.
- `python src/reproducibility_manifest.py` — **completed after the final source and documentation updates**.
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
- There is no verified prediction-time source workflow or later independent validation period. ElasticNet's best-CV selection has only a negligible holdout MAE difference from the baseline, with uncertainty spanning zero.
- No production refresh feed or deployed model exists; recurring drift monitoring and retraining are not applicable to the current offline evaluation.

These are evidence gaps, not passing criteria. The offline model evaluation does not establish a useful deployable predictor.

## Strategic planning additions

- The Strategic Recommendations page now estimates a two-arm sample size for a binary conversion test from a verified baseline rate, minimum detectable lift, significance level, and power. It states the independent-outcome assumptions and warns that clustering or attrition requires a design-specific calculation.
- The page also has an assumption-based monthly impact calculator for incremental conversions, net revenue, contribution after variable costs, campaign cost, and break-even lift. Inputs start at zero; the calculator does not use the unverified dataset to invent a baseline, lift, order value, or margin.
- The scenario and sample-size formulas live in `src/experiment_design.py`; unit tests cover boundary validation, negative-lift behavior, break-even math, and the effect of minimum detectable lift and statistical power.
- These tools improve planning and make the next experiment actionable. They do not create observed business impact or close the ROI evidence gate; validated attribution and finance data plus a controlled test remain necessary.

## Category uncertainty analysis

- `src/inference.py` now compares each post type and campaign type with all remaining categories using the weighted engagement-rate difference. It resamples paired seven-calendar-day moving blocks, reports simultaneous 95% intervals across category contrasts within each dimension, and returns no interval when too many bootstrap resamples lack a valid denominator.
- `src/run_descriptive_inference.py` generated `reports/category_rate_inference.json` from the exact 50,000-row app CSV (SHA-256 recorded in the report). The 5,000-replicate report includes three-, seven-, and fourteen-day block-length sensitivity; the dashboard calculates the seven-day analysis for active filters and exports the table.
- In the full-file analysis, the Image-versus-other-formats difference was -0.179 percentage points. Its simultaneous 95% interval stayed below zero across all three block lengths (3-day: [-0.300, -0.057]; 7-day: [-0.312, -0.046]; 14-day: [-0.318, -0.040]). Every campaign-versus-rest interval included zero across those block lengths.
- The Image contrast translates to an observed gap equivalent of about -440,736 engagements at Image's summed reach (seven-day 95% interval: about -767,521 to -113,951). This is the rate difference applied to the category's own reach, not a causal or incremental engagement estimate. Campaign equivalents are likewise descriptive only.
- This is an exploratory sample-specific association only. Multiplicity adjustment is within each dimension, not jointly across format and campaign families; the row grain and sample are unverified, dates may not be independent blocks, and confounding remains. Use the format observation as a pre-registered test hypothesis, not a content allocation decision.

## Attributed business impact workflow

- `BUSINESS_IMPACT_DATA_CONTRACT.md` defines the row grain, conversion denominator, attribution window/method, finance definitions, and optional randomized-arm fields. A blank header-only CSV template is provided in `data/business_impact_attribution_template.csv`.
- `src/business_impact.py` validates an uploaded export and calculates attributed conversion rate, customer acquisition cost, net ROAS, contribution, and ROI by format or campaign. If verified experiment fields are included, it estimates treatment-minus-control conversion-rate and net-contribution differences with a unit-level bootstrap interval.
- The Strategic Recommendations page accepts the CSV, surfaces validation failures, displays/downloads calculated results, and asks the owner to attest that assignment and measurement were preregistered before showing arm effects. Unit tests cover schema failures, accounting calculations, and the randomized-arm bootstrap.
- No attributed business outcome file is present in this repository. The workflow is implemented and tested, but the project still has no observed conversion, revenue, cost, or incremental ROI result; the data page states this explicitly. Do not fill the template with invented values.

## Assumed decision portfolio

- The in-dashboard portfolio in `pages/8_Strategic_Recommendations.py`, powered by `src/decision_portfolio.py`, defines three sequenced Marketing/Finance decisions: Image versus Reel creative, Tutorial versus Product Launch messaging, and current paid mix versus a capped tested-format reallocation.
- `python src/run_decision_portfolio.py` recalculates sample sizes and illustrative economics into `reports/assumed_decision_portfolio.json`. The plan uses a Bonferroni-adjusted two-sided alpha of 1.67% per test (5% family-wise), 80% power, and states that binary sample-size calculations do not power the continuous net-contribution outcome.
- Under the explicit assumed inputs only, required eligible units are 48,943, 132,559, and 28,156 per arm. At assumed monthly volumes, these correspond to roughly 2, 6, and 3 months. Scenario net contribution after assumed monthly costs is INR 58,750, INR 32,000, and INR 6,000 respectively. These are planning outputs, not observed ROI.
- The Strategic Recommendations page displays the hypotheses, comparison design, sample sizes, run-time estimates, guardrails, and actions for successful, inconclusive, or harmful results. Its randomized-arm analysis now allows the preregistered confidence level to be applied to both conversion and per-unit contribution intervals.
- No campaign was launched and no stakeholder supplied or approved these inputs. Use the plan to structure approvals and replace every assumed value before execution.

## Exposure-conditional engagement-volume model

- The Predictive Model Validation page retains the pre-publication engagement-rate evaluation and adds a separate model using existing observed reach and impressions to estimate total likes, comments, shares, and saves.
- `src/conditional_engagement_model.py` uses a Ridge regression and median baseline, four expanding date-grouped CV folds with a seven-day gap, and a latest-20%-of-dates holdout. It excludes target components and post-outcome annotations from inputs.
- The engagement-volume target and available exposure features were selected after reviewing this dataset. Therefore the holdout results are exploratory, not confirmatory evidence of generalizable model performance. On the 9,980-row later-date holdout, Ridge achieved MAE 1,240.34 engagements and R² 0.622, versus median-baseline MAE 2,119.57. The paired daily 95% interval for Ridge-minus-baseline MAE was [-915.77, -842.80].
- This estimate conditions on observed reach/impressions, so it describes current-post engagement volume rather than a pre-publication or causal forecast. Reports and row-level predictions are in `reports/conditional_engagement_volume.json` and `reports/conditional_engagement_volume_predictions.csv`.
