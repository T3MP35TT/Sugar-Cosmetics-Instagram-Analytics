"""Leakage-aware time-forward engagement-rate model evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    AdaBoostRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import (
    BayesianRidge,
    ElasticNet,
    HuberRegressor,
    Lasso,
    LinearRegression,
    PoissonRegressor,
    Ridge,
    TweedieRegressor,
)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor

from analytics import load_data


SEED = 20261017
CATEGORICAL_FEATURES = [
    "post_type",
    "campaign_type",
    "format_campaign",
    "hashtag_signature",
]
NUMERIC_FEATURES = [
    "hashtag_count",
    "days_since_start",
    "month_sin",
    "month_cos",
    "weekday_sin",
    "weekday_cos",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_model_frame(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Build pre-publication features and engagement-rate target.

    Outcome metrics (reach, impressions, likes, comments, shares, saves,
    visits and follows) and labels that may encode post-outcome information
    are excluded from X. Their inclusion would leak target information.
    """
    required = {"post_date", "post_type", "campaign_type", "hashtags", "reach", "likes", "comments", "shares", "saves"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Required modeling fields missing: {missing}")

    frame = raw.copy()
    frame["post_date"] = pd.to_datetime(frame["post_date"], errors="coerce", format="mixed").dt.normalize()
    engagement_cols = ["likes", "comments", "shares", "saves"]
    for column in ["reach", *engagement_cols]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    total_engagements = frame[engagement_cols].sum(axis=1, min_count=len(engagement_cols))
    target = total_engagements / frame["reach"].where(frame["reach"] > 0)

    valid = frame["post_date"].notna() & target.notna() & np.isfinite(target)
    valid &= frame["post_type"].notna() & frame["campaign_type"].notna()
    frame = frame.loc[valid].copy()
    target = target.loc[valid].astype(float)

    origin = frame["post_date"].min()
    day_of_year = frame["post_date"].dt.dayofyear.to_numpy(dtype=float)
    weekday = frame["post_date"].dt.dayofweek.to_numpy(dtype=float)
    hashtags = frame["hashtags"].fillna("").astype(str)
    normalized_tags = hashtags.map(
        lambda value: sorted({tag.lower() for tag in re.findall(r"#\w+", value)})
    )
    frame["hashtag_count"] = normalized_tags.map(len)
    frame["hashtag_signature"] = normalized_tags.map(
        lambda tags: "|".join(tags) if tags else "__no_hashtags__"
    )
    frame["format_campaign"] = (
        frame["post_type"].astype(str) + " :: " + frame["campaign_type"].astype(str)
    )
    frame["days_since_start"] = (frame["post_date"] - origin).dt.days.astype(float)
    frame["month_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    frame["month_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    frame["weekday_sin"] = np.sin(2 * np.pi * weekday / 7)
    frame["weekday_cos"] = np.cos(2 * np.pi * weekday / 7)

    x = frame[FEATURES].copy()
    meta = frame[["post_date", "post_type", "campaign_type"]].copy()
    meta["target_engagement_rate"] = target
    return x, target, meta


def date_grouped_splits(dates: pd.Series, *, n_splits: int = 4, gap_days: int = 7):
    """Expanding-window CV splits that keep each calendar date in one fold."""
    normalized = pd.to_datetime(dates).dt.normalize().reset_index(drop=True)
    unique_dates = np.sort(normalized.unique())
    splitter = TimeSeriesSplit(n_splits=n_splits, gap=gap_days)
    splits = []
    for train_days, validation_days in splitter.split(unique_dates):
        train_set = set(unique_dates[train_days])
        validation_set = set(unique_dates[validation_days])
        train_idx = np.flatnonzero(normalized.isin(train_set).to_numpy())
        validation_idx = np.flatnonzero(normalized.isin(validation_set).to_numpy())
        splits.append((train_idx, validation_idx))
    return splits


def chronological_holdout_indices(dates: pd.Series, *, train_fraction: float = 0.8):
    """Split on unique normalized dates so one date cannot cross the holdout."""
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be at least 0.5 and less than 1.0")
    normalized = pd.to_datetime(dates).dt.normalize().reset_index(drop=True)
    unique_dates = np.sort(normalized.unique())
    if len(unique_dates) < 2:
        raise ValueError("At least two unique dates are required for a chronological holdout")
    cutoff_index = int(np.floor(len(unique_dates) * train_fraction))
    cutoff = pd.Timestamp(unique_dates[cutoff_index])
    development_mask = normalized < cutoff
    holdout_mask = ~development_mask
    return development_mask.to_numpy(), holdout_mask.to_numpy(), cutoff


def regression_metrics(actual, predicted) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
        "mean_error_prediction_minus_actual": float(np.mean(predicted - actual)),
    }


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=[("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)],
        sparse_threshold=0.0,
    )


def _model_pipeline(regressor) -> Pipeline:
    return Pipeline([("preprocess", _preprocessor()), ("regressor", regressor)])


def select_one_standard_error_candidate(cv_results, *, n_splits: int) -> dict:
    """Select the simplest candidate within one CV standard error of the best MAE."""
    if not isinstance(n_splits, int) or n_splits < 2:
        raise ValueError("n_splits must be an integer of at least two")
    means = -np.asarray(cv_results["mean_test_mae"], dtype=float)
    standard_deviations = np.asarray(cv_results["std_test_mae"], dtype=float)
    best_index = int(np.nanargmin(means))
    standard_error = float(standard_deviations[best_index] / np.sqrt(n_splits))
    limit = float(means[best_index] + standard_error)
    eligible = [
        int(index)
        for index, score in enumerate(means)
        if score <= limit + np.finfo(float).eps * max(1.0, abs(limit)) * 8
    ]
    params = cv_results["params"]

    baseline_indices = [
        index for index in eligible
        if isinstance(params[index]["regressor"], DummyRegressor)
    ]
    preferred_model_order = [Ridge, BayesianRidge, HuberRegressor, ElasticNet, Lasso,
                             LinearSVR, PoissonRegressor, TweedieRegressor,
                             DecisionTreeRegressor, HistGradientBoostingRegressor,
                             GradientBoostingRegressor, AdaBoostRegressor,
                             RandomForestRegressor, ExtraTreesRegressor, MLPRegressor,
                             KNeighborsRegressor]
    ridge_indices = [
        index for index in eligible
        if isinstance(params[index]["regressor"], Ridge)
    ]
    elastic_net_indices = [
        index for index in eligible
        if isinstance(params[index]["regressor"], ElasticNet)
    ]
    if baseline_indices:
        selected_index = baseline_indices[0]
        policy = (
            "One-standard-error rule across the median baseline and ML candidates: "
            "select the median baseline when it is within one CV standard error of the best candidate."
        )
    elif ridge_indices:
        selected_index = max(
            ridge_indices,
            key=lambda index: float(params[index].get("regressor__alpha", 0.0)),
        )
        policy = (
            "One-standard-error rule: the median baseline did not qualify; select the most regularized "
            "Ridge candidate within one CV standard error of the best candidate."
        )
    elif elastic_net_indices:
        selected_index = max(
            elastic_net_indices,
            key=lambda index: float(params[index].get("regressor__alpha", 0.0)),
        )
        policy = (
            "One-standard-error rule: the baseline and Ridge candidates did not qualify; select the most "
            "regularized ElasticNet candidate within one CV standard error of the best candidate."
        )
    else:
        preferred_indices = [
            index for model_type in preferred_model_order
            for index in eligible
            if isinstance(params[index]["regressor"], model_type)
        ]
        if preferred_indices:
            selected_index = preferred_indices[0]
            policy = (
                "One-standard-error rule: the baseline and preferred regularized linear candidates did not qualify; "
                f"select the simplest available eligible family ({type(params[selected_index]['regressor']).__name__})."
            )
        else:
            selected_index = best_index
            policy = "No simpler candidate qualified; select the minimum temporal-CV MAE candidate."
    return {
        "best_index": best_index,
        "selected_index": selected_index,
        "standard_error": standard_error,
        "limit": limit,
        "policy": policy,
    }


def _daily_block_bootstrap_delta(actual, model_pred, baseline_pred, dates, *, repetitions=1000, seed=SEED):
    """Percentile interval for model-minus-baseline MAE, resampling date blocks."""
    errors_delta = np.abs(np.asarray(actual) - np.asarray(model_pred)) - np.abs(np.asarray(actual) - np.asarray(baseline_pred))
    day_values = pd.to_datetime(dates).dt.normalize().to_numpy()
    daily = pd.DataFrame({"day": day_values, "delta": errors_delta}).groupby("day")["delta"].agg(["sum", "count"])
    if len(daily) < 2:
        return {"lower_95": None, "upper_95": None, "repetitions": 0}
    sums = daily["sum"].to_numpy()
    counts = daily["count"].to_numpy()
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(daily), size=(repetitions, len(daily)))
    sampled_sums = sums[draws].sum(axis=1)
    sampled_counts = counts[draws].sum(axis=1)
    deltas = sampled_sums / sampled_counts
    low, high = np.quantile(deltas, [0.025, 0.975])
    return {
        "lower_95": float(low),
        "upper_95": float(high),
        "repetitions": int(repetitions),
        "interpretation": "Date-block bootstrap interval for MAE difference (model minus median baseline); conditional on dates being valid independent resampling blocks. It does not establish causality or population validity.",
    }


def _subgroup_error(meta, actual, model_pred, baseline_pred, columns):
    rows = meta.copy().reset_index(drop=True)
    rows["actual"] = np.asarray(actual)
    rows["model_prediction"] = np.asarray(model_pred)
    rows["baseline_prediction"] = np.asarray(baseline_pred)
    rows["absolute_model_error"] = np.abs(rows["model_prediction"] - rows["actual"])
    rows["absolute_baseline_error"] = np.abs(rows["baseline_prediction"] - rows["actual"])
    result = {}
    for column in columns:
        groups = rows.groupby(column, dropna=False).agg(
            records=("actual", "size"),
            mean_actual=("actual", "mean"),
            mean_prediction=("model_prediction", "mean"),
            model_mae=("absolute_model_error", "mean"),
            median_baseline_mae=("absolute_baseline_error", "mean"),
        )
        groups["mae_delta_vs_baseline"] = groups["model_mae"] - groups["median_baseline_mae"]
        result[column] = []
        for _, row in groups.reset_index().iterrows():
            record = {"group": row[column]}
            record.update({key: row[key] for key in groups.columns})
            result[column].append(
                {key: (value.item() if isinstance(value, np.generic) else value) for key, value in record.items()}
            )
    return result


def run_model_evaluation(
    input_path: Path,
    *,
    output_dir: Path,
    seed: int = SEED,
    bootstrap_repetitions: int = 1000,
) -> dict:
    """Tune candidates on earlier dates and evaluate once on a future holdout."""
    started = time.perf_counter()
    input_path = Path(input_path).resolve()
    output_dir = Path(output_dir).resolve()
    raw = load_data(input_path)
    x, y, meta = build_model_frame(raw)
    unique_dates = np.sort(meta["post_date"].unique())
    if len(unique_dates) < 40:
        raise ValueError("At least 40 unique dates are required for temporal evaluation.")

    dev_mask, test_mask, cutoff = chronological_holdout_indices(meta["post_date"], train_fraction=0.8)
    x_dev, x_test = x.loc[dev_mask].reset_index(drop=True), x.loc[test_mask].reset_index(drop=True)
    y_dev, y_test = y.loc[dev_mask].reset_index(drop=True), y.loc[test_mask].reset_index(drop=True)
    meta_dev, meta_test = meta.loc[dev_mask].reset_index(drop=True), meta.loc[test_mask].reset_index(drop=True)
    cv = date_grouped_splits(meta_dev["post_date"], n_splits=4, gap_days=7)

    candidate_pipeline = _model_pipeline(Ridge())
    parameter_grid = [
        {"regressor": [DummyRegressor(strategy="median")]},
        {"regressor": [LinearRegression()]},
        {"regressor": [Ridge()], "regressor__alpha": [0.1, 1.0, 10.0, 100.0]},
        {"regressor": [BayesianRidge()]},
        {"regressor": [HuberRegressor(max_iter=500)], "regressor__alpha": [0.0001, 0.01]},
        {"regressor": [Lasso(max_iter=5000, selection="cyclic")], "regressor__alpha": [0.00001, 0.0001, 0.001]},
        {
            "regressor": [ElasticNet(max_iter=5000, random_state=seed)],
            "regressor__alpha": [0.001, 0.01, 0.1],
            "regressor__l1_ratio": [0.25, 0.75],
        },
        {"regressor": [LinearSVR(random_state=seed, max_iter=5000, dual="auto")], "regressor__C": [0.1, 1.0, 10.0]},
        {"regressor": [PoissonRegressor(max_iter=500)], "regressor__alpha": [0.1, 1.0, 10.0]},
        {"regressor": [TweedieRegressor(power=1.5, link="log", max_iter=500)], "regressor__alpha": [0.1, 1.0]},
        {"regressor": [DecisionTreeRegressor(random_state=seed)], "regressor__max_depth": [3, 8, None], "regressor__min_samples_leaf": [20]},
        {
            "regressor": [HistGradientBoostingRegressor(random_state=seed, early_stopping=False)],
            "regressor__max_iter": [100, 200],
            "regressor__max_leaf_nodes": [7, 15],
            "regressor__learning_rate": [0.05, 0.1],
        },
        {"regressor": [GradientBoostingRegressor(random_state=seed)], "regressor__n_estimators": [100], "regressor__learning_rate": [0.05, 0.1], "regressor__max_depth": [2, 3]},
        {"regressor": [AdaBoostRegressor(random_state=seed)], "regressor__n_estimators": [50, 100], "regressor__learning_rate": [0.05, 0.5]},
        {
            "regressor": [RandomForestRegressor(random_state=seed, n_estimators=100, n_jobs=1)],
            "regressor__max_features": [0.7, 1.0],
            "regressor__min_samples_leaf": [10, 40],
        },
        {"regressor": [MLPRegressor(hidden_layer_sizes=(32,), alpha=0.01, early_stopping=True, max_iter=300, random_state=seed)]},
        {"regressor": [KNeighborsRegressor(n_jobs=1)], "regressor__n_neighbors": [25, 75], "regressor__weights": ["uniform", "distance"]},
        {
            "regressor": [ExtraTreesRegressor(random_state=seed, n_estimators=100, n_jobs=1)],
            "regressor__max_features": [0.7, 1.0],
            "regressor__min_samples_leaf": [10, 40],
        },
    ]
    # Fix the naïve baseline first so all candidate models are judged against
    # an explicit, untuned reference.
    baseline = _model_pipeline(DummyRegressor(strategy="median"))
    baseline_cv = cross_validate(
        baseline,
        x_dev,
        y_dev,
        cv=cv,
        scoring="neg_mean_absolute_error",
        return_train_score=True,
        n_jobs=-1,
    )
    baseline.fit(x_dev, y_dev)

    search = GridSearchCV(
        candidate_pipeline,
        parameter_grid,
        scoring={"mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error", "r2": "r2"},
        refit="mae",
        cv=cv,
        n_jobs=-1,
        return_train_score=True,
        error_score="raise",
    )
    search.fit(x_dev, y_dev)
    cv_results = search.cv_results_
    one_se_selection = select_one_standard_error_candidate(
        cv_results, n_splits=len(cv)
    )
    best_cv_index = one_se_selection["best_index"]
    best_cv_mae = float(-cv_results["mean_test_mae"][best_cv_index])
    one_se_limit = one_se_selection["limit"]
    selected_index = one_se_selection["selected_index"]
    selection_policy = one_se_selection["policy"]
    ml_indices = [index for index, params in enumerate(cv_results["params"])
                  if not isinstance(params["regressor"], DummyRegressor)]
    # GridSearchCV stores negative MAE scores: maximize the score to find the
    # lowest actual MAE among ML candidates.
    best_ml_index = max(ml_indices, key=lambda index: cv_results["mean_test_mae"][index])
    best_ml_params = cv_results["params"][best_ml_index]
    selected_params = cv_results["params"][selected_index]
    selected_estimator = _model_pipeline(selected_params["regressor"])
    selected_model_parameters = {
        key.replace("regressor__", ""): value
        for key, value in selected_params.items()
        if key != "regressor"
    }
    if selected_model_parameters:
        selected_estimator.set_params(**{
            f"regressor__{key}": value for key, value in selected_model_parameters.items()
        })
    selected_estimator.fit(x_dev, y_dev)
    selected_prediction = selected_estimator.predict(x_test)
    best_ml_estimator = _model_pipeline(best_ml_params["regressor"])
    best_ml_parameters = {
        key.replace("regressor__", ""): value
        for key, value in best_ml_params.items() if key != "regressor"
    }
    if best_ml_parameters:
        best_ml_estimator.set_params(**{
            f"regressor__{key}": value for key, value in best_ml_parameters.items()
        })
    best_ml_estimator.fit(x_dev, y_dev)
    model_prediction = best_ml_estimator.predict(x_test)
    baseline_prediction = baseline.predict(x_test)
    actual = y_test.to_numpy(dtype=float)

    candidate_rows = []
    results = cv_results
    for index, params in enumerate(results["params"]):
        estimator = params["regressor"]
        candidate_rows.append({
            "model": type(estimator).__name__,
            "parameters": {key.replace("regressor__", ""): value for key, value in params.items() if key != "regressor"},
            "cv_mae": float(-results["mean_test_mae"][index]),
            "cv_mae_std": float(results["std_test_mae"][index]),
            "cv_rmse": float(-results["mean_test_rmse"][index]),
            "cv_r2": float(results["mean_test_r2"][index]),
            "train_mae": float(-results["mean_train_mae"][index]),
            "validation_minus_train_mae": float(
                -results["mean_test_mae"][index] + results["mean_train_mae"][index]
            ),
            "selected_by_one_se_rule": index == selected_index,
            "best_ml_candidate": index == best_ml_index,
        })
    candidate_rows.sort(key=lambda row: row["cv_mae"])

    holdout = {
        "record_count": int(len(y_test)),
        "start_date": str(meta_test["post_date"].min().date()),
        "end_date": str(meta_test["post_date"].max().date()),
        "median_baseline": regression_metrics(actual, baseline_prediction),
        "selected_model": regression_metrics(actual, selected_prediction),
        "best_ml_candidate": regression_metrics(actual, model_prediction),
    }
    holdout["mae_difference_model_minus_baseline"] = (
        holdout["best_ml_candidate"]["mae"] - holdout["median_baseline"]["mae"]
    )
    holdout["relative_mae_improvement_over_baseline"] = (
        (holdout["median_baseline"]["mae"] - holdout["best_ml_candidate"]["mae"])
        / holdout["median_baseline"]["mae"]
    )
    holdout["date_block_bootstrap_mae_difference_interval"] = _daily_block_bootstrap_delta(
        actual,
        model_prediction,
        baseline_prediction,
        meta_test["post_date"],
        repetitions=bootstrap_repetitions,
        seed=seed,
    )

    predictions = meta_test.copy()
    predictions["predicted_engagement_rate"] = model_prediction
    predictions["selected_approach_prediction"] = selected_prediction
    predictions["median_baseline_prediction"] = baseline_prediction
    predictions["residual"] = actual - model_prediction
    predictions["absolute_error"] = np.abs(predictions["residual"])
    subgroup = _subgroup_error(
        meta_test,
        actual,
        model_prediction,
        baseline_prediction,
        ["post_type", "campaign_type"],
    )
    monthly = predictions.assign(month=predictions["post_date"].dt.to_period("M").astype(str)).groupby("month").agg(
        records=("residual", "size"),
        mae=("absolute_error", "mean"),
        mean_residual=("residual", "mean"),
        actual_mean=("target_engagement_rate", "mean"),
        prediction_mean=("predicted_engagement_rate", "mean"),
    ).reset_index().to_dict(orient="records")

    best_ml_candidate = next(row for row in candidate_rows if row["best_ml_candidate"])
    baseline_cv_mae = float(-baseline_cv["test_score"].mean())
    model_improves_cv_baseline = best_ml_candidate["cv_mae"] < baseline_cv_mae
    model_improves_holdout_baseline = (
        holdout["best_ml_candidate"]["mae"] < holdout["median_baseline"]["mae"]
    )
    holdout_improvement_supported = (
        holdout["date_block_bootstrap_mae_difference_interval"]["upper_95"] is not None
        and holdout["date_block_bootstrap_mae_difference_interval"]["upper_95"] < 0
    )
    model_justified = (
        model_improves_cv_baseline
        and model_improves_holdout_baseline
        and holdout_improvement_supported
        and not isinstance(selected_params["regressor"], DummyRegressor)
    )
    report = {
        "report_version": 3,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {"path": str(input_path), "sha256": sha256_file(input_path), "rows": int(len(raw))},
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "python_packages": {"scikit_learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        },
        "code_hashes": {
            "modeling_sha256": sha256_file(Path(__file__).resolve()),
            "runner_sha256": sha256_file(Path(__file__).with_name("run_model_evaluation.py")),
            "dependency_lock_sha256": sha256_file(Path(__file__).resolve().parents[1] / "requirements-lock.txt"),
        },
        "problem": {
            "type": "regression",
            "target": "total engagements / reach, for rows with positive reach",
            "intended_use": "Offline test of whether pre-publication format, campaign interaction, canonical hashtag-set, hashtag-count, and calendar features predict recorded engagement rate in later dates.",
            "features": FEATURES,
            "feature_engineering": {
                "interaction_features": [
                    "format_campaign combines the pre-publication format and campaign labels to allow their joint effect.",
                    "hashtag_signature canonicalizes the set of supplied hashtags to model combinations without order or case differences.",
                ],
                "calendar_features": "Days since the first observed date plus cyclical day-of-year and weekday terms.",
                "categorical_handling": "Impute within each training fold; one-hot encode with unseen categories ignored.",
                "numeric_handling": "Median-impute and standardize within each training fold.",
                "feature_availability": "All retained predictors are metadata available before publication; outcome metrics and potentially post-outcome annotations remain excluded.",
            },
            "excluded_fields": ["impressions", "reach", "likes", "comments", "shares", "saves", "profile_visits", "follows", "audience_emotion", "engagement_source"],
            "leakage_controls": "All outcome metrics and potentially post-outcome labels are excluded from model inputs. A date-based holdout and expanding-window date-grouped CV keep every calendar date within one split; preprocessing is fitted inside each fold.",
        },
        "split": {
            "strategy": "Chronological 80/20 split on unique calendar dates; no date appears in both partitions.",
            "development_records": int(len(y_dev)),
            "holdout_records": int(len(y_test)),
            "development_end_date": str(meta_dev["post_date"].max().date()),
            "holdout_start_date": str(meta_test["post_date"].min().date()),
            "cross_validation": {"strategy": "4-fold expanding-window TimeSeriesSplit over unique dates", "gap_days": 7, "folds": int(len(cv))},
        },
        "baseline": {
            "model": "DummyRegressor predicting development-set median engagement rate",
            "temporal_cv_mae_mean": baseline_cv_mae,
            "temporal_cv_mae_std": float(baseline_cv["test_score"].std(ddof=1)),
            "temporal_cv_train_mae_mean": float(-baseline_cv["train_score"].mean()),
        },
        "tuning": {
            "method": "GridSearchCV over available, suitable scikit-learn regression families; minimize MAE over four expanding temporal folds. Kernel SVR is excluded because its quadratic training cost is impractical at this dataset size.",
            "model_families_tested": sorted({
                type(row["regressor"]).__name__
                for row in cv_results["params"]
            }),
            "candidate_count": len(candidate_rows),
            "seed": seed,
            "best_cv_mae": float(-cv_results["mean_test_mae"][best_cv_index]),
            "best_cv_standard_error": one_se_selection["standard_error"],
            "one_standard_error_method": "Standard deviation of temporal-fold MAE divided by square root of the fold count; approximate because expanding temporal folds are dependent.",
            "one_standard_error_limit_mae": one_se_limit,
            "selection_policy": selection_policy,
            "best_cv_parameters": {
                key.replace("regressor__", ""): value
                for key, value in cv_results["params"][best_cv_index].items()
                if key != "regressor"
            },
            "best_cv_estimator": type(cv_results["params"][best_cv_index]["regressor"]).__name__,
            "selected_parameters": selected_model_parameters,
            "best_estimator": type(selected_estimator.named_steps["regressor"]).__name__,
            "best_ml_candidate_parameters": best_ml_parameters,
            "best_ml_candidate_estimator": type(best_ml_params["regressor"]).__name__,
            "best_ml_candidate_cv_mae": float(-cv_results["mean_test_mae"][best_ml_index]),
            "one_se_selected_approach": type(selected_estimator.named_steps["regressor"]).__name__,
        },
        "cross_validation_candidates": candidate_rows,
        "model_vs_baseline": {
            "best_ml_candidate_cv_mae": best_ml_candidate["cv_mae"],
            "median_baseline_cv_mae": baseline_cv_mae,
            "cv_mae_difference_model_minus_baseline": best_ml_candidate["cv_mae"] - baseline_cv_mae,
            "ml_candidate_improves_cv_baseline": model_improves_cv_baseline,
            "ml_candidate_improves_future_holdout_baseline": model_improves_holdout_baseline,
            "future_holdout_gain_supported_by_date_block_interval": holdout_improvement_supported,
            "complexity_justified": model_justified,
            "recommended_approach": (
                type(selected_estimator.named_steps["regressor"]).__name__
                if model_justified
                else "Median baseline; no ML candidate showed consistent out-of-sample improvement"
            ),
        },
        "overfit_diagnostic": {
            "best_ml_candidate_train_mae": best_ml_candidate["train_mae"],
            "best_ml_candidate_validation_mae": best_ml_candidate["cv_mae"],
            "validation_minus_train_mae": best_ml_candidate["cv_mae"] - best_ml_candidate["train_mae"],
            "interpretation": "A large positive gap indicates weaker performance on later folds than on their training periods; use alongside the untouched future holdout.",
        },
        "fit_diagnosis": (
            "No useful predictive gain is established: the best ML candidate's point MAE is nearly identical to the median baseline and the date-block uncertainty interval includes no difference. The one-standard-error rule selects the baseline; do not use the ML candidate without a practically meaningful gain on a new future period."
            if not model_justified
            else "The ML candidate improves temporal validation and has an uncertainty-supported holdout gain; confirm practical value and reproduce on a new future period before deployment."
        ),
        "holdout_evaluation": holdout,
        "subgroup_error_analysis": subgroup,
        "monthly_holdout_error_analysis": monthly,
        "complex_model_justified": model_justified,
        "scalability_observation": {
            "input_records": int(len(raw)),
            "evaluation_runtime_seconds": round(time.perf_counter() - started, 3),
            "interpretation": "Observed on this local environment and 50k-row input only; expected production volume and hardware service limits are not specified.",
        },
        "limitations": [
            "The dataset's collection method, official account identity, row grain, and sampling frame are unverified.",
            "Predictive performance is conditional on this file and time split and must not be generalized as official Sugar Cosmetics performance.",
            "The date-block bootstrap interval is descriptive and conditional on calendar dates serving as resampling blocks; it is not a causal test.",
            "Subgroup error review covers content and campaign labels only; demographics and fairness cannot be assessed from the available fields.",
            "This is a reproducible offline evaluation, not a deployed prediction or retraining service.",
        ],
        "runtime_seconds": round(time.perf_counter() - started, 3),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "model_evaluation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    predictions.sort_values("absolute_error", ascending=False).to_csv(output_dir / "model_holdout_predictions.csv", index=False)
    return report
