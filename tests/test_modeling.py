import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from modeling import (  # noqa: E402
    CATEGORICAL_FEATURES,
    FEATURES,
    build_model_frame,
    chronological_holdout_indices,
    date_grouped_splits,
    regression_metrics,
)


def make_model_data(days=60):
    dates = pd.date_range("2025-01-01", periods=days, freq="D").repeat(2)
    return pd.DataFrame(
        {
            "post_date": dates,
            "post_type": ["Reel", "Image"] * days,
            "campaign_type": ["Launch", "Tutorial"] * days,
            "hashtags": ["#beauty #makeup", "#beauty"] * days,
            "impressions": [1000, 800] * days,
            "reach": [800, 600] * days,
            "likes": [80, 60] * days,
            "comments": [8, 6] * days,
            "shares": [4, 3] * days,
            "saves": [8, 6] * days,
            "profile_visits": [40, 30] * days,
            "follows": [8, 6] * days,
            "audience_emotion": ["happy", "curious"] * days,
            "engagement_source": ["organic", "organic"] * days,
        }
    )


def test_model_features_exclude_outcomes_and_derived_post_outcome_labels():
    raw = make_model_data()
    features, target, metadata = build_model_frame(raw)
    assert set(features.columns) == set(FEATURES)
    assert set(CATEGORICAL_FEATURES).issubset(features.columns)
    assert not set(raw.columns).intersection(features.columns) - set(CATEGORICAL_FEATURES)
    assert len(features) == len(target) == len(metadata)
    assert np.allclose(target, 100 / 800)
    assert metadata["post_date"].is_monotonic_increasing


def test_date_grouped_cross_validation_has_no_shared_days_and_respects_time_order():
    dates = pd.Series(pd.date_range("2025-01-01", periods=80, freq="D").repeat(2))
    splits = date_grouped_splits(dates, n_splits=4, gap_days=7)
    assert len(splits) == 4
    for train_idx, validation_idx in splits:
        train_days = set(dates.iloc[train_idx])
        validation_days = set(dates.iloc[validation_idx])
        assert train_days.isdisjoint(validation_days)
        assert max(train_days) < min(validation_days)
        assert (min(validation_days) - max(train_days)).days >= 8


def test_chronological_holdout_keeps_repeated_calendar_dates_together():
    dates = pd.Series(pd.date_range("2025-01-01", periods=50, freq="D").repeat(3))
    development, holdout, cutoff = chronological_holdout_indices(dates)
    assert not (development & holdout).any()
    assert (development | holdout).all()
    assert dates.loc[development].max() < cutoff
    assert dates.loc[holdout].min() == cutoff
    assert set(dates.loc[development]).isdisjoint(set(dates.loc[holdout]))


def test_regression_metrics_are_calculated_and_json_safe():
    metrics = regression_metrics([0.1, 0.2, 0.3], [0.1, 0.1, 0.4])
    assert np.isclose(metrics["mae"], 1 / 15)
    assert np.isclose(metrics["rmse"], np.sqrt(0.02 / 3))
    assert np.isclose(metrics["mean_error_prediction_minus_actual"], 0)
