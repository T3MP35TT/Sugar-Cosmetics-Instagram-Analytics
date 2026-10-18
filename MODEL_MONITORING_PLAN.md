# Predictive model monitoring and retraining plan

## Current release decision

The engagement-rate model is an offline evaluation only. The strongest ML candidate is ElasticNet (alpha 0.01, L1 ratio 0.25). On the 9,980-record temporal holdout, its MAE (0.06223515) is effectively tied with the median baseline (0.06223522); the date-block 95% interval for the MAE difference is [-0.00000734, 0.00000724] and includes zero. The one-standard-error rule selects the median baseline. **Do not deploy or use the ML candidate for content, budget, or business decisions.** This plan becomes active only if a later model passes the deployment gates below.

## Pre-deployment gates

1. The data owner confirms a stable row ID, one-row grain, source account, metric definitions, and capture timestamp.
2. The marketing owner confirms that post type, campaign type, hashtag count, and calendar fields are available at the moment a forecast would be made.
3. Obtain a later, independently collected period. Keep it untouched until model and alert thresholds are approved.
4. The candidate must improve the agreed primary metric over a simple baseline on temporal validation and the untouched period. Approve minimum useful improvement and error limits before opening that period.
5. Review overall and subgroup errors, calibration by engagement-rate band, data-quality checks, and the model's intended action with business and engineering owners.
6. Record the model version, feature contract, source hashes, Python/dependency versions, evaluation results, approvers, and rollback owner.

## Checks for each scored batch

- Validate required fields, types, allowed category values, missingness, date coverage, duplicate IDs, and impossible metric relationships. Reject the batch when the contract fails.
- Record input and model hashes, batch time, row count, feature summaries, prediction coverage, and output checksum.
- Compare feature distributions and category shares with the approved training reference. Alert using limits calibrated from a verified baseline period; do not choose arbitrary drift thresholds after seeing an incident.
- Once outcomes mature, calculate MAE, RMSE, mean signed error, and calibration by month and approved subgroups. Compare against both the deployed model's acceptance limits and the baseline.
- Suppress predictions for unknown or invalid records; route validation failures and alert events to the named owner.

## Cadence and response

- Run schema, missingness, range, and prediction-coverage checks on every batch.
- Review feature drift weekly and matured outcome/error metrics monthly, or sooner when the business owner requires it.
- When a pre-approved limit is crossed, pause decision use, fall back to the documented descriptive report/baseline, investigate data and process changes, and record the incident.
- Retrain only after enough verified new data accumulates and a material change is diagnosed. Repeat date-ordered cross-validation and a fresh untouched future evaluation. Never reuse a holdout for tuning.
- Resume predictions only after the model passes the same pre-approved acceptance gates and the business and engineering owners sign off. Keep the prior approved model and baseline available for rollback.

## Ownership to assign before activation

The data owner maintains source contracts; the analytics owner maintains features, evaluation, and retraining; the engineering owner runs batch checks and rollback; the marketing owner approves targets, thresholds, and the business action. No owner, recurring feed, alert channel, or production model is configured in the current repository.
