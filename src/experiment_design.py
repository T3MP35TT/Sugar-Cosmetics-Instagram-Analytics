"""Pure calculations for conversion-test planning and business scenarios."""

from math import ceil, isfinite, sqrt
from statistics import NormalDist


def estimate_two_proportion_sample_size(
    baseline_rate,
    minimum_detectable_lift,
    *,
    alpha=0.05,
    power=0.8,
):
    """Estimate equal per-arm size for a two-sided independent binary-outcome test.

    Rates, alpha, and power are proportions in [0, 1]. Uses the common normal
    approximation with pooled null variance and unpooled alternative variance.
    It does not adjust for clustering, attrition, multiple outcomes, or
    noncompliance.
    """
    values = (baseline_rate, minimum_detectable_lift, alpha, power)
    if not all(isfinite(value) for value in values):
        raise ValueError("All inputs must be finite numbers")
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if minimum_detectable_lift <= 0:
        raise ValueError("minimum_detectable_lift must be positive")
    treatment_rate = baseline_rate + minimum_detectable_lift
    if treatment_rate >= 1:
        raise ValueError("baseline_rate plus lift must be below 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0.5 <= power < 1:
        raise ValueError("power must be at least 0.5 and below 1")

    pooled = (baseline_rate + treatment_rate) / 2
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    variance_term = (
        z_alpha * sqrt(2 * pooled * (1 - pooled))
        + z_power
        * sqrt(
            baseline_rate * (1 - baseline_rate)
            + treatment_rate * (1 - treatment_rate)
        )
    )
    per_arm = ceil(variance_term**2 / minimum_detectable_lift**2)
    return {"per_arm": per_arm, "total": 2 * per_arm}


def estimate_business_impact(
    monthly_opportunities,
    baseline_conversion_rate,
    absolute_lift,
    net_revenue_per_conversion,
    contribution_margin,
    incremental_campaign_cost,
):
    """Calculate a scenario from supplied assumptions; this is not observed ROI.

    Rates are proportions in [0, 1], margin is a proportion, and amounts use
    the same currency. Lift is an absolute conversion-rate change.
    """
    values = (
        monthly_opportunities,
        baseline_conversion_rate,
        absolute_lift,
        net_revenue_per_conversion,
        contribution_margin,
        incremental_campaign_cost,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("All inputs must be finite numbers")
    if monthly_opportunities < 0:
        raise ValueError("monthly_opportunities cannot be negative")
    if not 0 <= baseline_conversion_rate <= 1:
        raise ValueError("baseline_conversion_rate must be between 0 and 1")
    scenario_rate = baseline_conversion_rate + absolute_lift
    if not 0 <= scenario_rate <= 1:
        raise ValueError("baseline rate plus lift must be between 0 and 1")
    if net_revenue_per_conversion < 0:
        raise ValueError("net_revenue_per_conversion cannot be negative")
    if not 0 <= contribution_margin <= 1:
        raise ValueError("contribution_margin must be between 0 and 1")
    if incremental_campaign_cost < 0:
        raise ValueError("incremental_campaign_cost cannot be negative")

    incremental_conversions = monthly_opportunities * absolute_lift
    incremental_revenue = incremental_conversions * net_revenue_per_conversion
    incremental_contribution = incremental_revenue * contribution_margin
    net_contribution = incremental_contribution - incremental_campaign_cost
    break_even_lift = None
    contribution_capacity = (
        monthly_opportunities * net_revenue_per_conversion * contribution_margin
    )
    if contribution_capacity > 0:
        break_even_lift = incremental_campaign_cost / contribution_capacity

    return {
        "scenario_conversion_rate": scenario_rate,
        "incremental_conversions": incremental_conversions,
        "incremental_net_revenue": incremental_revenue,
        "incremental_contribution": incremental_contribution,
        "incremental_campaign_cost": incremental_campaign_cost,
        "net_contribution_after_cost": net_contribution,
        "break_even_absolute_lift": break_even_lift,
    }
