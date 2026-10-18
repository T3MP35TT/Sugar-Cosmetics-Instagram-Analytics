"""Evaluate engagement-volume estimates conditional on observed post exposure."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from analytics import load_data
from modeling import chronological_holdout_indices, date_grouped_splits


NUMERIC_FEATURES = ["reach", "impressions", "hashtag_count"]
CATEGORICAL_FEATURES = ["post_type", "campaign_type"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
SEED = 20261017


def _pipeline(regressor) -> Pipeline:
    numeric = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    transform = ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)]
    )
    return Pipeline([("preprocess", transform), ("regressor", regressor)])


def _metrics(actual, predicted) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
        "mean_prediction": float(np.mean(predicted)),
        "prediction_std": float(np.std(predicted)),
    }


def _paired_daily_interval(actual, model_prediction, baseline_prediction, dates, *, reps=2000):
    delta = np.abs(np.asarray(actual) - np.asarray(model_prediction)) - np.abs(
        np.asarray(actual) - np.asarray(baseline_prediction)
    )
    daily = pd.DataFrame(
        {"date": pd.to_datetime(dates).dt.normalize().to_numpy(), "delta": delta}
    ).groupby("date")["delta"].agg(["sum", "count"])
    if len(daily) < 2:
        return {"lower_95": None, "upper_95": None, "repetitions": 0}
    rng = np.random.default_rng(SEED)
    sums, counts = daily["sum"].to_numpy(), daily["count"].to_numpy()
    draws = rng.integers(0, len(daily), size=(reps, len(daily)))
    values = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    lower, upper = np.quantile(values, [0.025, 0.975])
    return {
        "lower_95": float(lower),
        "upper_95": float(upper),
        "repetitions": reps,
        "interpretation": "Paired daily bootstrap interval for Ridge-minus-median-baseline MAE; conditional on calendar dates as resampling blocks.",
    }


def evaluate_conditional_engagement_volume(input_path: Path, output_dir: Path) -> dict:
    """Estimate interaction volume when reach and impressions are observed.

    This is a conditional estimate after distribution/exposure is known; it is
    not a pre-publication forecast. Engagement counts are not model features.
    """
    input_path, output_dir = Path(input_path), Path(output_dir)
    raw = load_data(input_path)
    work = raw.copy()
    work["hashtag_count"] = work["hashtags"].fillna("").astype(str).str.findall(r"#\w+").str.len()
    work["total_engagements"] = work[["likes", "comments", "shares", "saves"]].sum(
        axis=1, min_count=4
    )
    valid = work["post_date"].notna() & work["total_engagements"].notna()
    valid &= work["reach"].gt(0) & work["impressions"].gt(0)
    valid &= work["post_type"].notna() & work["campaign_type"].notna()
    work = work.loc[valid].sort_values("post_date").reset_index(drop=True)
    x, y, dates = work[FEATURES], work["total_engagements"], work["post_date"]
    dev_mask, test_mask, cutoff = chronological_holdout_indices(dates, train_fraction=0.8)
    x_dev, x_test = x.loc[dev_mask], x.loc[test_mask]
    y_dev, y_test = y.loc[dev_mask], y.loc[test_mask]
    dates_dev, dates_test = dates.loc[dev_mask], dates.loc[test_mask]
    cv = date_grouped_splits(dates_dev, n_splits=4, gap_days=7)

    cv_rows = []
    for model_name, estimator in [
        ("Median baseline", DummyRegressor(strategy="median")),
        ("Ridge regression", Ridge(alpha=1.0)),
    ]:
        fold_maes = []
        for train_idx, validation_idx in cv:
            fitted = _pipeline(estimator.__class__(**estimator.get_params()))
            fitted.fit(x_dev.iloc[train_idx], y_dev.iloc[train_idx])
            fold_maes.append(
                float(mean_absolute_error(y_dev.iloc[validation_idx], fitted.predict(x_dev.iloc[validation_idx])))
            )
        cv_rows.append(
            {
                "model": model_name,
                "fold_mae": fold_maes,
                "mean_mae": float(np.mean(fold_maes)),
                "std_mae": float(np.std(fold_maes, ddof=1)),
            }
        )

    baseline = _pipeline(DummyRegressor(strategy="median")).fit(x_dev, y_dev)
    ridge = _pipeline(Ridge(alpha=1.0)).fit(x_dev, y_dev)
    baseline_prediction = baseline.predict(x_test)
    prediction = ridge.predict(x_test)
    actual = y_test.to_numpy(dtype=float)
    baseline_metrics = _metrics(actual, baseline_prediction)
    ridge_metrics = _metrics(actual, prediction)
    predictions = work.loc[test_mask, ["post_date", "post_type", "campaign_type"]].copy()
    predictions["actual_engagements"] = actual
    predictions["predicted_engagements"] = prediction
    predictions["median_baseline_prediction"] = baseline_prediction
    predictions["residual"] = actual - prediction
    predictions["absolute_error"] = np.abs(predictions["residual"])
    predictions["reach"] = x_test["reach"].to_numpy()
    predictions["impressions"] = x_test["impressions"].to_numpy()
    predictions["month"] = predictions["post_date"].dt.to_period("M").astype(str)
    subgroup_validation = {}
    for dimension in ["post_type", "campaign_type"]:
        grouped = predictions.groupby(dimension).agg(
            records=("actual_engagements", "size"),
            actual_mean=("actual_engagements", "mean"),
            prediction_mean=("predicted_engagements", "mean"),
            mae=("absolute_error", "mean"),
            mean_error=("residual", "mean"),
        ).reset_index()
        subgroup_validation[dimension] = grouped.to_dict(orient="records")
    monthly = predictions.groupby("month").agg(
        records=("actual_engagements", "size"),
        actual_mean=("actual_engagements", "mean"),
        prediction_mean=("predicted_engagements", "mean"),
        mae=("absolute_error", "mean"),
    ).reset_index()
    interval = _paired_daily_interval(actual, prediction, baseline_prediction, dates_test)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {"path": str(input_path.resolve()), "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(), "rows": int(len(raw))},
        "target": "likes + comments + shares + saves (engagement volume)",
        "analysis_status": "Exploratory; target and inputs were selected after reviewing this dataset, so reported holdout performance is descriptive and should not be treated as confirmatory model-selection evidence.",
        "intended_use": "Estimate engagement count conditional on observed reach and impressions for analysis of existing posts; not a pre-publication forecast.",
        "features": FEATURES,
        "excluded_features": ["likes", "comments", "shares", "saves", "profile_visits", "follows", "audience_emotion", "engagement_source"],
        "split": {
            "strategy": "Chronological holdout on unique dates; four expanding date-grouped folds with a 7-day gap for development-only validation.",
            "development_records": int(dev_mask.sum()),
            "holdout_records": int(test_mask.sum()),
            "cutoff_date": str(cutoff.date()),
            "holdout_start": str(dates_test.min().date()),
            "holdout_end": str(dates_test.max().date()),
            "cv_folds": cv_rows,
        },
        "holdout": {
            "median_baseline": baseline_metrics,
            "ridge": ridge_metrics,
            "mae_difference_ridge_minus_baseline": ridge_metrics["mae"] - baseline_metrics["mae"],
            "relative_mae_reduction": (baseline_metrics["mae"] - ridge_metrics["mae"]) / baseline_metrics["mae"],
            "daily_bootstrap_mae_difference_interval": interval,
        },
        "monthly": monthly.to_dict(orient="records"),
        "subgroup_validation": subgroup_validation,
        "prediction_file": "conditional_engagement_volume_predictions.csv",
        "model": "Ridge(alpha=1.0), selected as a regularized linear conditional estimator; no test-set tuning.",
        "limitations": "Predictions condition on realized reach and impressions, which are observed exposure measures. They describe conditional association in this dataset and do not establish causal lift or pre-publication performance.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conditional_engagement_volume.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    predictions.sort_values("absolute_error", ascending=False).to_csv(
        output_dir / report["prediction_file"], index=False
    )
    return report
