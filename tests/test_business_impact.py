import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest

from business_impact import (
    aggregate_business_impact,
    compare_randomized_arms,
    validate_attribution_data,
)


def attribution_data():
    rows = []
    for arm, conversions in (("control", [1, 2, 3, 4]), ("treatment", [3, 4, 5, 6])):
        for index, count in enumerate(conversions):
            rows.append(
                {
                    "post_id": f"{arm}-{index}",
                    "post_date": f"2025-02-{index + 1:02d}",
                    "post_type": "Reel" if index % 2 else "Image",
                    "campaign_type": "Test",
                    "eligible_opportunities": 100,
                    "attributed_conversions": count,
                    "attributed_net_revenue": count * 100,
                    "variable_cost": count * 30,
                    "paid_media_cost": 50,
                    "currency_code": "INR",
                    "attribution_window_days": 7,
                    "attribution_method": "last_click",
                    "randomization_unit_id": f"{arm}-unit-{index}",
                    "experiment_arm": arm,
                }
            )
    return pd.DataFrame(rows)


def test_valid_attribution_data_passes_contract():
    result = validate_attribution_data(attribution_data())
    assert result["valid"]
    assert result["rows"] == 8
    assert result["currency_code"] == "INR"
    assert result["experiment_fields_available"]


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda df: df.drop(columns="post_id"), "Missing required columns"),
        (lambda df: pd.concat([df, df.iloc[[0]]], ignore_index=True), "post_id must be unique"),
        (
            lambda df: df.assign(attributed_conversions=1000),
            "cannot exceed eligible_opportunities",
        ),
        (lambda df: df.assign(currency_code="US"), "three-letter codes"),
        (lambda df: df.assign(attribution_window_days=0), "greater than zero"),
        (lambda df: df.assign(paid_media_cost=-1), "cannot contain negative values"),
    ],
)
def test_invalid_attribution_data_fails_with_actionable_error(mutate, expected):
    result = validate_attribution_data(mutate(attribution_data()))
    assert not result["valid"]
    assert any(expected in error for error in result["errors"])


def test_aggregation_calculates_actual_observed_cost_and_revenue_metrics():
    result = aggregate_business_impact(attribution_data(), "campaign_type").iloc[0]
    assert result["records"] == 8
    assert result["eligible_opportunities"] == 800
    assert result["attributed_conversions"] == 28
    assert result["attributed_net_revenue"] == 2800
    assert result["variable_cost"] == 840
    assert result["paid_media_cost"] == 400
    assert result["net_contribution"] == 1560
    assert result["conversion_rate"] == pytest.approx(0.035)
    assert result["customer_acquisition_cost"] == pytest.approx(400 / 28)
    assert result["net_roas"] == pytest.approx(7)
    assert result["roi"] == pytest.approx(3.9)


def test_arm_comparison_uses_randomization_units_and_reproducible_intervals():
    data = attribution_data()
    result = compare_randomized_arms(data, bootstrap_reps=500, random_state=17)
    repeated = compare_randomized_arms(data, bootstrap_reps=500, random_state=17)
    assert result == repeated
    assert result["control_units"] == result["treatment_units"] == 4
    assert result["treatment_minus_control_conversion_rate_pp"] == pytest.approx(2)
    assert result["net_contribution_difference_per_unit"] == pytest.approx(140)
    assert result["conversion_rate_difference_ci_low_pp"] <= 2
    assert result["conversion_rate_difference_ci_high_pp"] >= 2
    assert "conditional on verified random assignment" in result["interpretation"]


def test_arm_comparison_requires_both_arms_and_multiple_units():
    data = attribution_data()
    incomplete = pd.concat(
        [
            data.loc[data["experiment_arm"].eq("control")].iloc[:1],
            data.loc[data["experiment_arm"].eq("treatment")],
        ],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="two randomized units"):
        compare_randomized_arms(incomplete)


def test_arm_comparison_requires_pre_treatment_denominator_for_each_unit():
    data = attribution_data()
    data.loc[0, "eligible_opportunities"] = 0
    data.loc[0, "attributed_conversions"] = 0
    with pytest.raises(ValueError, match="pre-treatment outcome denominator"):
        compare_randomized_arms(data)


def test_aggregate_rejects_unknown_dimension_and_invalid_data():
    with pytest.raises(ValueError, match="dimension must be"):
        aggregate_business_impact(attribution_data(), "unknown")
    with pytest.raises(ValueError, match="Invalid attribution data"):
        aggregate_business_impact(attribution_data().drop(columns="campaign_type"), "post_type")
