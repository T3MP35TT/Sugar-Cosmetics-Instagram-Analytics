import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import pytest

from inference import category_rate_contrasts


def daily_category_data(days=42):
    rows = []
    for offset, date in enumerate(pd.date_range("2025-01-01", periods=days)):
        for category, likes in (("A", 10 + offset % 4), ("B", 20 + offset % 3)):
            rows.append(
                {
                    "post_date": date,
                    "post_type": category,
                    "reach": 100,
                    "total_engagements": likes,
                }
            )
    return pd.DataFrame(rows)


def test_category_contrasts_compare_weighted_rates_to_all_other_categories():
    result = category_rate_contrasts(
        daily_category_data(), "post_type", bootstrap_reps=300, random_state=7
    ).set_index("post_type")
    assert result.loc["A", "records"] == 42
    assert result.loc["A", "other_records"] == 42
    assert result.loc["A", "weighted_rate"] == pytest.approx(
        result.loc["A", "engagements"] / result.loc["A", "reach"]
    )
    assert result.loc["A", "difference_pp"] < 0
    assert result.loc["B", "difference_pp"] > 0
    assert result.loc["A", "simultaneous_ci_low_pp"] <= result.loc["A", "difference_pp"]
    assert result.loc["A", "simultaneous_ci_high_pp"] >= result.loc["A", "difference_pp"]
    assert result.loc["A", "engagement_gap_equivalent"] == pytest.approx(
        result.loc["A", "difference_pp"] / 100 * result.loc["A", "reach"]
    )
    assert result.loc["A", "engagement_gap_equivalent_ci_low"] == pytest.approx(
        result.loc["A", "simultaneous_ci_low_pp"] / 100 * result.loc["A", "reach"]
    )
    assert result.loc["A", "engagement_gap_equivalent_ci_high"] == pytest.approx(
        result.loc["A", "simultaneous_ci_high_pp"] / 100 * result.loc["A", "reach"]
    )


def test_category_contrast_bootstrap_is_reproducible():
    data = daily_category_data()
    first = category_rate_contrasts(data, "post_type", bootstrap_reps=300, random_state=19)
    second = category_rate_contrasts(data, "post_type", bootstrap_reps=300, random_state=19)
    pd.testing.assert_frame_equal(first, second)


def test_category_contrasts_filter_invalid_rows_and_keep_calendar_gaps():
    data = daily_category_data()
    data.loc[0, "reach"] = 0
    data.loc[1, "post_date"] = pd.NaT
    result = category_rate_contrasts(data, "post_type", bootstrap_reps=300)
    assert result["records"].sum() == len(data) - 2
    eligible = data["reach"].gt(0) & data["post_date"].notna()
    assert result["reach"].sum() == data.loc[eligible, "reach"].sum()


def test_single_category_has_no_other_group_or_interval():
    data = daily_category_data()
    data = data.loc[data["post_type"].eq("A")]
    result = category_rate_contrasts(data, "post_type", bootstrap_reps=300)
    assert result.loc[0, "other_records"] == 0
    assert np.isnan(result.loc[0, "other_weighted_rate"])
    assert np.isnan(result.loc[0, "simultaneous_ci_low_pp"])


def test_empty_eligible_input_returns_schema():
    data = daily_category_data()
    data["reach"] = 0
    result = category_rate_contrasts(data, "post_type", bootstrap_reps=300)
    assert result.empty
    assert "simultaneous_ci_low_pp" in result.columns


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bootstrap_reps": 99},
        {"confidence_level": 1},
        {"block_days": 0},
    ],
)
def test_category_contrasts_reject_invalid_bootstrap_settings(kwargs):
    with pytest.raises(ValueError):
        category_rate_contrasts(daily_category_data(), "post_type", **kwargs)


def test_category_contrasts_reject_missing_columns():
    with pytest.raises(ValueError, match="Required columns missing"):
        category_rate_contrasts(pd.DataFrame({"post_type": ["A"]}), "post_type")
