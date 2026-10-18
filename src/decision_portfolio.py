"""Illustrative, preregistration-ready business decision scenarios.

All numeric values below are planning assumptions supplied for the example
portfolio. They are not estimates from the Instagram dataset or actual SUGAR
Cosmetics finance records. Replace them with owner-approved values before use.
"""

from math import ceil

from experiment_design import estimate_business_impact, estimate_two_proportion_sample_size


PORTFOLIO_ASSUMPTIONS = {
    "currency": "INR",
    "family_alpha": 0.05,
    "power": 0.80,
    "decisions": [
        {
            "sequence": 1,
            "sponsor": "Marketing",
            "decision": "Creative format: Image or Reel",
            "hypothesis": "A Reel-led creative generates a commercially useful increase in attributed purchase conversion versus an Image-led creative.",
            "comparison": "Randomly split eligible audience into Image (control) and Reel (treatment); hold offer, audience, spend, placement, and measurement window constant.",
            "randomization_unit": "Mutually exclusive platform audience members assigned before exposure.",
            "primary_outcome": "Attributed purchase conversions / pre-treatment eligible audience members (intention to treat).",
            "guardrails": "Net contribution per assigned member, paid cost per purchase, reach delivery, negative feedback, and brand-safety review.",
            "baseline_conversion_rate": 0.020,
            "minimum_detectable_lift": 0.003,
            "monthly_opportunities": 50000,
            "net_revenue_per_conversion": 1500.0,
            "contribution_margin": 0.35,
            "incremental_campaign_cost": 20000.0,
            "success_action": "If lift is at least 0.30 percentage points, its Bonferroni-adjusted two-sided 98.33% interval excludes zero, net contribution is positive with its preregistered uncertainty interval excluding zero, and guardrails pass, shift at most 10% of the next comparable test budget to Reels, then replicate.",
            "inconclusive_action": "Keep the current allocation; do not call a winner. Re-estimate power only after checking delivery, contamination, and outcome maturity.",
            "harm_action": "Stop the treatment and return to the control if the pre-agreed harm boundary is crossed or net contribution is negative at the fixed analysis.",
        },
        {
            "sequence": 2,
            "sponsor": "Marketing",
            "decision": "Campaign message: Tutorial or Product Launch",
            "hypothesis": "A Tutorial message increases attributed purchase conversion versus a Product Launch message when format, offer, and audience are held constant.",
            "comparison": "Randomize eligible audience to Tutorial (control) or Product Launch (treatment) messaging using the same creative format and offer.",
            "randomization_unit": "Mutually exclusive platform audience members assigned before exposure.",
            "primary_outcome": "Attributed purchase conversions / pre-treatment eligible audience members (intention to treat).",
            "guardrails": "Net contribution per assigned member, paid cost per purchase, reach delivery, negative feedback, and brand-safety review.",
            "baseline_conversion_rate": 0.025,
            "minimum_detectable_lift": 0.002,
            "monthly_opportunities": 50000,
            "net_revenue_per_conversion": 1200.0,
            "contribution_margin": 0.35,
            "incremental_campaign_cost": 10000.0,
            "success_action": "If lift is at least 0.20 percentage points, its Bonferroni-adjusted two-sided 98.33% interval excludes zero, net contribution is positive with its preregistered uncertainty interval excluding zero, and guardrails pass, use the Product Launch message in a limited rollout and replicate.",
            "inconclusive_action": "Keep the current message mix; refine the hypothesis or collect a properly powered new test rather than selecting the higher observed rate.",
            "harm_action": "Stop the treatment and return to the control if the pre-agreed harm boundary is crossed or net contribution is negative at the fixed analysis.",
        },
        {
            "sequence": 3,
            "sponsor": "Finance + Marketing",
            "decision": "Paid allocation: current mix or tested-format reallocation",
            "hypothesis": "A capped 10% reallocation toward the winning tested format increases net contribution per assigned audience member at the same total spend.",
            "comparison": "Randomize mutually exclusive audience cells to the current paid mix (control) or proposed mix (treatment); keep total spend, eligibility, and campaign window equal.",
            "randomization_unit": "Mutually exclusive audience cells assigned before paid exposure; recalculate power for any cluster-level assignment.",
            "primary_outcome": "Attributed purchase conversions / pre-treatment assigned audience members; net contribution after paid media cost per assigned member is the Finance scale-up gate (the sample-size calculation does not power this continuous outcome).",
            "guardrails": "Attributed purchase conversion rate, cost per purchase, spend cap, reach delivery, negative feedback, and brand safety.",
            "baseline_conversion_rate": 0.020,
            "minimum_detectable_lift": 0.004,
            "monthly_opportunities": 20000,
            "net_revenue_per_conversion": 1500.0,
            "contribution_margin": 0.30,
            "incremental_campaign_cost": 30000.0,
            "success_action": "If the conversion lift reaches 0.40 percentage points with its Bonferroni-adjusted two-sided 98.33% interval excluding zero, net contribution is positive with its preregistered uncertainty interval excluding zero, conversion and spend guardrails pass, and Finance reconciles the costs, roll out the 10% reallocation for one cycle and review again.",
            "inconclusive_action": "Retain the current mix and spend cap; do not reallocate based on engagement or attributed ROAS alone.",
            "harm_action": "Revert to the control mix immediately if the approved spend cap or harm guardrail is breached.",
        },
    ],
}


def build_decision_portfolio() -> dict:
    """Calculate sample-size and monthly impact scenarios from explicit assumptions."""
    results = []
    per_test_alpha = PORTFOLIO_ASSUMPTIONS["family_alpha"] / len(
        PORTFOLIO_ASSUMPTIONS["decisions"]
    )
    for decision in PORTFOLIO_ASSUMPTIONS["decisions"]:
        sample = estimate_two_proportion_sample_size(
            decision["baseline_conversion_rate"],
            decision["minimum_detectable_lift"],
            alpha=per_test_alpha,
            power=PORTFOLIO_ASSUMPTIONS["power"],
        )
        impact = estimate_business_impact(
            monthly_opportunities=decision["monthly_opportunities"],
            baseline_conversion_rate=decision["baseline_conversion_rate"],
            absolute_lift=decision["minimum_detectable_lift"],
            net_revenue_per_conversion=decision["net_revenue_per_conversion"],
            contribution_margin=decision["contribution_margin"],
            incremental_campaign_cost=decision["incremental_campaign_cost"],
        )
        results.append({
            **decision,
            "testwise_alpha": per_test_alpha,
            "sample_size": sample,
            "estimated_months_at_assumed_volume": ceil(
                sample["total"] / decision["monthly_opportunities"]
            ),
            "impact_scenario": impact,
        })

    return {
        "status": "illustrative planning only; assumptions are not observed data or stakeholder approvals",
        "currency": PORTFOLIO_ASSUMPTIONS["currency"],
        "familywise_alpha": PORTFOLIO_ASSUMPTIONS["family_alpha"],
        "testwise_alpha_bonferroni": per_test_alpha,
        "power": PORTFOLIO_ASSUMPTIONS["power"],
        "assumptions_notice": (
            "Conversion rates, minimum lifts, opportunity counts, net revenue, margin, and campaign costs are hypothetical. "
            "Three decision tests use a Bonferroni per-test alpha to control family-wise two-sided error at 5%. "
            "The calculation assumes independent binary outcomes, equal assignment, no clustering, and no attrition. "
            "Replace with reconciled source-system data and approved finance inputs before launch."
        ),
        "decisions": results,
    }
