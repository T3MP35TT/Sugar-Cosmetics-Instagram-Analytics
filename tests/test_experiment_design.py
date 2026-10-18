import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from experiment_design import (
    estimate_business_impact,
    estimate_two_proportion_sample_size,
)


def test_two_proportion_sample_size_returns_equal_arms_and_uses_inputs():
    result = estimate_two_proportion_sample_size(
        baseline_rate=0.02,
        minimum_detectable_lift=0.005,
        alpha=0.05,
        power=0.8,
    )
    assert result["per_arm"] > 0
    assert result["total"] == 2 * result["per_arm"]


def test_sample_size_increases_for_smaller_lift_or_higher_power():
    standard = estimate_two_proportion_sample_size(0.02, 0.005)
    smaller_lift = estimate_two_proportion_sample_size(0.02, 0.003)
    higher_power = estimate_two_proportion_sample_size(0.02, 0.005, power=0.9)
    assert smaller_lift["total"] > standard["total"]
    assert higher_power["total"] > standard["total"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"baseline_rate": 0, "minimum_detectable_lift": 0.01},
        {"baseline_rate": 0.99, "minimum_detectable_lift": 0.02},
        {"baseline_rate": 0.1, "minimum_detectable_lift": 0},
        {"baseline_rate": 0.1, "minimum_detectable_lift": 0.02, "alpha": 1},
        {"baseline_rate": 0.1, "minimum_detectable_lift": 0.02, "power": 0.4},
    ],
)
def test_sample_size_rejects_invalid_assumptions(kwargs):
    with pytest.raises(ValueError):
        estimate_two_proportion_sample_size(**kwargs)


def test_business_impact_scenario_calculates_incremental_value_and_break_even():
    result = estimate_business_impact(
        monthly_opportunities=100_000,
        baseline_conversion_rate=0.02,
        absolute_lift=0.005,
        net_revenue_per_conversion=500,
        contribution_margin=0.4,
        incremental_campaign_cost=1_000,
    )
    assert result["scenario_conversion_rate"] == pytest.approx(0.025)
    assert result["incremental_conversions"] == pytest.approx(500)
    assert result["incremental_net_revenue"] == pytest.approx(250_000)
    assert result["incremental_contribution"] == pytest.approx(100_000)
    assert result["net_contribution_after_cost"] == pytest.approx(99_000)
    assert result["break_even_absolute_lift"] == pytest.approx(0.00005)


def test_negative_lift_is_reflected_as_negative_incremental_value():
    result = estimate_business_impact(
        monthly_opportunities=10_000,
        baseline_conversion_rate=0.05,
        absolute_lift=-0.01,
        net_revenue_per_conversion=100,
        contribution_margin=0.5,
        incremental_campaign_cost=0,
    )
    assert result["scenario_conversion_rate"] == pytest.approx(0.04)
    assert result["incremental_conversions"] == pytest.approx(-100)
    assert result["net_contribution_after_cost"] == pytest.approx(-5_000)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"monthly_opportunities": -1},
        {"baseline_conversion_rate": 1.1},
        {"absolute_lift": 0.1, "baseline_conversion_rate": 0.95},
        {"net_revenue_per_conversion": -1},
        {"contribution_margin": 1.1},
        {"incremental_campaign_cost": -1},
    ],
)
def test_business_impact_rejects_invalid_inputs(kwargs):
    assumptions = {
        "monthly_opportunities": 1000,
        "baseline_conversion_rate": 0.02,
        "absolute_lift": 0.005,
        "net_revenue_per_conversion": 100,
        "contribution_margin": 0.5,
        "incremental_campaign_cost": 100,
    }
    assumptions.update(kwargs)
    with pytest.raises(ValueError):
        estimate_business_impact(**assumptions)
