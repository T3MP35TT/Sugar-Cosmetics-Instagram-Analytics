from pathlib import Path
import json
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize
from analytics import category_performance
from business_impact import (
    aggregate_business_impact,
    compare_randomized_arms,
    validate_attribution_data,
)
from decision_portfolio import build_decision_portfolio
from experiment_design import (
    estimate_business_impact,
    estimate_two_proportion_sample_size,
)
from inference import category_rate_contrasts


context = initialize("Strategic Recommendations")
globals().update(context)
render_sidebar_summary("Strategic Recommendations", f)

with st.container(border=True):
    st.subheader("Selected scope summary")
    page_kpis("Strategic Recommendations", f)
    st.info(
        "Decision rule: use these observational comparisons to choose a test hypothesis. "
        "Keep the audience, goal, paid support, and measurement window comparable; change strategy only after a pre-agreed test outcome supports it."
    )


@st.cache_data(show_spinner=False)
def _cached_category_contrasts(data, dimension):
    return category_rate_contrasts(
        data, dimension, bootstrap_reps=2000, block_days=7, random_state=42
    )


with st.container(border=True):
    st.subheader("Observed patterns and test candidates")
    st.caption(
        "The supplied records support descriptive comparisons. They do not identify a causal winner. "
        "The likely upstream file source is documented in DATA_PROVENANCE.md. Confirm collection method and row grain before treating this as brand performance."
    )

    if f.empty:
        st.warning("No records match the current data selection. Widen the date range or filters to compare formats.")
    else:
        grouped = category_performance(f, "post_type")
        action_totals = (
            f.groupby("post_type", dropna=False)
            .agg(
                saves=("saves", lambda values: values.sum(min_count=1)),
                shares=("shares", lambda values: values.sum(min_count=1)),
                visits=("profile_visits", lambda values: values.sum(min_count=1)),
                follows=("follows", lambda values: values.sum(min_count=1)),
            )
            .reset_index()
        )
        grouped = grouped.merge(action_totals, on="post_type", how="left", validate="one_to_one")
        grouped["save_rate_proxy"] = grouped["saves"] / grouped["reach"].where(grouped["reach"] > 0)
        grouped["share_rate_proxy"] = grouped["shares"] / grouped["reach"].where(grouped["reach"] > 0)
        grouped["follow_per_visit_proxy"] = grouped["follows"] / grouped["visits"].where(grouped["visits"] > 0)
        display = grouped.rename(
            columns={
                "post_type": "Format",
                "records": "Records",
                "reach": "Summed reach",
                "engagements": "Engagements",
                "mean_record_rate": "Mean record engagement rate",
                "weighted_engagement_rate": "Weighted engagement rate",
                "selected_scope_baseline": "Selected-scope baseline",
                "difference_from_baseline_pp": "Difference vs baseline (pp)",
                "save_rate_proxy": "Saves / reach proxy",
                "share_rate_proxy": "Shares / reach proxy",
                "follow_per_visit_proxy": "Follows / visits proxy",
            }
        )
        st.dataframe(
            display[
                [
                    "Format",
                    "Records",
                    "Summed reach",
                    "Mean record engagement rate",
                    "Weighted engagement rate",
                    "Selected-scope baseline",
                    "Difference vs baseline (pp)",
                    "Saves / reach proxy",
                    "Shares / reach proxy",
                    "Follows / visits proxy",
                ]
            ].style.format(
                {
                    "Summed reach": "{:,.0f}",
                    "Mean record engagement rate": "{:.2%}",
                    "Weighted engagement rate": "{:.2%}",
                    "Selected-scope baseline": "{:.2%}",
                    "Difference vs baseline (pp)": "{:+.2f}",
                    "Saves / reach proxy": "{:.2%}",
                    "Shares / reach proxy": "{:.2%}",
                    "Follows / visits proxy": "{:.2%}",
                },
                na_rep="—",
            ),
            width="stretch",
            hide_index=True,
        )

        st.subheader("Uncertainty around category differences")
        st.caption(
            "Each category is compared with all other categories using weighted engagements ÷ summed post-level reach. "
            "Intervals use 2,000 paired calendar-date bootstrap resamples with simultaneous 95% coverage across "
            "categories in each comparison. Resampling uses circular seven-day calendar blocks to retain short-term "
            "dependence. The interval adjustment is within each dimension, not joint across formats and campaigns. "
            "They are conditional on dates being valid resampling blocks; they do not "
            "adjust for confounding, validate the sample, or establish causality."
        )
        for dimension, label, category_name in [
            ("post_type", "Post type", "Format"),
            ("campaign_type", "Campaign type", "Campaign"),
        ]:
            with st.expander(f"{label} rate contrasts", expanded=(dimension == "post_type")):
                contrast = _cached_category_contrasts(f, dimension)
                if contrast.empty:
                    st.info(f"No eligible {label.lower()} records are available in the current filter.")
                    continue
                separated = contrast.loc[
                    contrast["simultaneous_ci_low_pp"].gt(0)
                    | contrast["simultaneous_ci_high_pp"].lt(0)
                ]
                if separated.empty:
                    st.info(
                        "No category-versus-rest interval excludes zero in this filtered view. "
                        "Treat the ranking as unresolved and use a controlled test to choose a winner."
                    )
                else:
                    candidates = ", ".join(
                        f"{row[dimension]} ({row['difference_pp']:+.2f} pp, "
                        f"95% [{row['simultaneous_ci_low_pp']:+.2f}, "
                        f"{row['simultaneous_ci_high_pp']:+.2f}])"
                        for _, row in separated.iterrows()
                    )
                    st.warning(
                        f"Sample-specific contrasts with intervals excluding zero: {candidates}. "
                        "These are hypotheses to test, not causal effects or budget recommendations."
                    )
                contrast = contrast.rename(
                    columns={
                        dimension: category_name,
                        "records": "Eligible records",
                        "weighted_rate": "Category weighted rate",
                        "other_records": "Other eligible records",
                        "other_weighted_rate": "Other categories weighted rate",
                        "difference_pp": "Difference (pp)",
                        "simultaneous_ci_low_pp": "95% interval low (pp)",
                        "simultaneous_ci_high_pp": "95% interval high (pp)",
                        "engagement_gap_equivalent": "Observed gap equivalent",
                        "engagement_gap_equivalent_ci_low": "Gap interval low",
                        "engagement_gap_equivalent_ci_high": "Gap interval high",
                    }
                )
                plot_data = contrast.dropna(
                    subset=["95% interval low (pp)", "95% interval high (pp)"]
                )
                if not plot_data.empty:
                    interval_plot = go.Figure(
                        go.Scatter(
                            x=plot_data["Difference (pp)"],
                            y=plot_data[category_name],
                            mode="markers",
                            marker=dict(size=10, color=SUGAR_PINK),
                            error_x=dict(
                                type="data",
                                symmetric=False,
                                array=(
                                    plot_data["95% interval high (pp)"]
                                    - plot_data["Difference (pp)"]
                                ),
                                arrayminus=(
                                    plot_data["Difference (pp)"]
                                    - plot_data["95% interval low (pp)"]
                                ),
                                color=SUGAR_MUTED,
                                thickness=2,
                                width=5,
                            ),
                            hovertemplate=(
                                "%{y}<br>Difference: %{x:+.2f} pp"
                                "<extra></extra>"
                            ),
                        )
                    )
                    interval_plot.add_vline(x=0, line_dash="dash", line_color=SUGAR_MUTED)
                    interval_plot.update_layout(
                        title=f"{label}: weighted rate difference vs all other categories",
                        xaxis_title="Difference in percentage points (95% simultaneous interval)",
                        yaxis_title="",
                        height=max(260, 75 * len(plot_data)),
                        margin=dict(l=12, r=20, t=55, b=45),
                        template="sugar",
                    )
                    st.plotly_chart(interval_plot, width="stretch")
                st.dataframe(
                    contrast[
                        [
                            category_name,
                            "Eligible records",
                            "Category weighted rate",
                            "Other eligible records",
                            "Other categories weighted rate",
                            "Difference (pp)",
                            "95% interval low (pp)",
                            "95% interval high (pp)",
                            "Observed gap equivalent",
                            "Gap interval low",
                            "Gap interval high",
                        ]
                    ].style.format(
                        {
                            "Eligible records": "{:,.0f}",
                            "Other eligible records": "{:,.0f}",
                            "Category weighted rate": "{:.2%}",
                            "Other categories weighted rate": "{:.2%}",
                            "Difference (pp)": "{:+.2f}",
                            "95% interval low (pp)": "{:+.2f}",
                            "95% interval high (pp)": "{:+.2f}",
                            "Observed gap equivalent": "{:+,.0f}",
                            "Gap interval low": "{:+,.0f}",
                            "Gap interval high": "{:+,.0f}",
                        },
                        na_rep="—",
                    ),
                    width="stretch",
                    hide_index=True,
                )
                st.caption(
                    "Observed gap equivalent = rate difference applied to this category's summed reach; it is a descriptive scale conversion, not incremental or causal engagements. "
                    "An interval spanning zero means the observed contrast is uncertain under this resampling method. "
                    "An interval excluding zero still describes association only; use a controlled test before changing strategy."
                )
                st.download_button(
                    f"Download {label.lower()} contrasts",
                    data=contrast.to_csv(index=False).encode("utf-8"),
                    file_name=f"{dimension}_rate_contrasts.csv",
                    mime="text/csv",
                    key=f"download_{dimension}_contrasts",
                )

    format_contrasts = _cached_category_contrasts(f, "post_type")
    positive_candidates = format_contrasts.loc[
        format_contrasts["simultaneous_ci_low_pp"].gt(0)
    ].sort_values("difference_pp", ascending=False)
    if positive_candidates.empty:
        st.info(
            "Recommended next step: this filtered view does not identify a format with a positive simultaneous interval. "
            "Use a controlled test to resolve the format choice; do not shift budget based on the current ranking."
        )
    else:
        candidate = positive_candidates.iloc[0]
        st.info(
            f"Test hypothesis: {candidate['post_type']} has an observed rate difference of "
            f"{candidate['difference_pp']:+.2f} pp versus other formats "
            f"(95% simultaneous interval [{candidate['simultaneous_ci_low_pp']:+.2f}, "
            f"{candidate['simultaneous_ci_high_pp']:+.2f}] pp). Validate it in a controlled test before changing strategy."
        )

with st.container(border=True):
    st.subheader("Experiment plan")
    st.caption("A practical four-step plan for turning an observed pattern into a decision-quality test.")
    design_steps = st.columns(4)
    for column, number, title, description in zip(
        design_steps,
        ["01", "02", "03", "04"],
        ["Frame", "Design", "Measure", "Decide"],
        [
            "State the audience, business goal, and specific hypothesis.",
            "Randomize independent units and keep treatment exposure comparable.",
            "Choose one primary outcome, guardrails, and an agreed sample size.",
            "Use the preregistered threshold; report effects and uncertainty.",
        ],
    ):
        with column:
            st.markdown(f"**{number} · {title}**")
            st.caption(description)
    with st.expander("Full preregistration checklist", expanded=False):
        st.markdown(
            """
    | Decision item | Specify before launch |
    |---|---|
    | Hypothesis | Choose one audience and campaign goal; state why the tested format should change the outcome. |
    | Randomization unit | Assign independent audience, campaign, or matched-content units. Prevent one unit from entering both arms; clustered exposure needs a design-specific power calculation. |
    | Treatment and comparison | Hold objective, paid support, audience eligibility, creative effort, and measurement window comparable; record deviations. |
    | Primary outcome | Preselect one: weighted engagement rate, saves per reach, shares per reach, or a validated attributed conversion rate. Define numerator, denominator, and attribution window. |
    | Guardrails | Track reach, negative feedback, spend, and brand-safety measures. Set harm limits before launch. |
    | Baseline and target | Use validated historical data and agree the minimum useful change with the marketing owner. Do not use this unverified file as the baseline. |
    | Sample and stopping rule | Use the planner only for independent binary outcomes; account for attrition and clustering separately. Set sample and end date before launch; do not stop early for favorable interim results. |
    | Analysis plan | Analyze assigned units by intention to treat, state missing-data rules, report effect size and interval, and treat unplanned subgroup checks as exploratory. |
    | Decision | Adopt only if the result clears the pre-agreed useful-lift and guardrail thresholds. Report uncertainty and limitations; replicate when the result is uncertain. |
    """
        )

with st.container(border=True):
    st.subheader("Assumed Marketing + Finance decision portfolio")
    portfolio = build_decision_portfolio()
    st.info(
        "Planning exercise only. The decision owners and values below are assumed so the tests can be sized and their economics illustrated. "
        "They are not stakeholder approvals, observed conversion rates, or actual SUGAR Cosmetics financial results. Replace every assumption before launch."
    )
    st.caption(
        "Run the three planned tests in sequence. Sample sizes use a Bonferroni-adjusted two-sided alpha of 1.67% per test (5% family-wise across the portfolio) and 80% power; do not pool sample sizes or expose the same audience to overlapping tests. "
        "The sample calculation assumes equal allocation, independent binary outcomes, no clustering, and no attrition."
    )
    phase_cols = st.columns(3)
    for item in portfolio["decisions"]:
        sample = item["sample_size"]
        impact = item["impact_scenario"]
        with phase_cols[item["sequence"] - 1]:
            with st.container(border=True):
                st.caption(f"PHASE {item['sequence']} · {item['sponsor']}")
                st.markdown(f"#### {item['decision']}")
                st.write(item["hypothesis"])
                metric_cols = st.columns(2)
                metric_cols[0].metric("Required sample", f"{sample['total']:,}", f"{sample['per_arm']:,} per arm")
                metric_cols[1].metric("Estimated duration", f"{item['estimated_months_at_assumed_volume']} mo.", "before outcome maturation")
                st.metric("Illustrative net contribution", f"INR {impact['net_contribution_after_cost']:,.0f}/month", "assumption-based scenario")
                st.caption(
                    f"Assumed baseline {item['baseline_conversion_rate']:.2%} · "
                    f"minimum detectable lift {item['minimum_detectable_lift'] * 100:.2f} pp · "
                    f"{item['monthly_opportunities']:,} eligible opportunities/month"
                )
    for item in portfolio["decisions"]:
        sample = item["sample_size"]
        impact = item["impact_scenario"]
        with st.expander(f"Phase {item['sequence']} experiment setup and decision rules", expanded=item["sequence"] == 1):
            st.write(f"**Hypothesis:** {item['hypothesis']}")
            setup_cols = st.columns(3)
            setup_cols[0].write(f"**Comparison**: {item['comparison']}")
            setup_cols[1].write(f"**Randomization unit**: {item['randomization_unit']}")
            setup_cols[2].write(f"**Primary outcome**: {item['primary_outcome']}")
            st.write(f"**Guardrails:** {item['guardrails']}")
            st.caption(
                f"Plan {sample['per_arm']:,} eligible units per arm ({sample['total']:,} total). "
                f"At assumed volume, allow about {item['estimated_months_at_assumed_volume']} months plus the outcome-maturation window. "
                f"Illustrative break-even lift: {impact['break_even_absolute_lift'] * 100:.3f} percentage points."
            )
            action_cols = st.columns(3)
            action_cols[0].success(f"**Scale if successful:** {item['success_action']}")
            action_cols[1].info(f"**Hold / learn if inconclusive:** {item['inconclusive_action']}")
            action_cols[2].error(f"**Stop or roll back if harmful:** {item['harm_action']}")
            if item["sequence"] == 3:
                st.warning("The sample-size calculation powers the binary conversion outcome only. It does not establish power for the continuous net-contribution outcome; Finance and Analytics must set that outcome's variance-based power requirement before launch.")
    st.download_button(
        "Download calculated portfolio (JSON)",
        data=json.dumps(portfolio, indent=2, allow_nan=False).encode("utf-8"),
        file_name="assumed_decision_portfolio.json",
        mime="application/json",
        key="download_assumed_decision_portfolio",
        width="stretch",
    )
    st.caption(
        "Scenario calculations are not observed impact. Confirm attribution, currency, sample feasibility, randomization, "
        "guardrails, the fixed end date, and named owners with Marketing, Finance, and Analytics before activating a test."
    )

with st.container(border=True):
    st.subheader("Planning scenario")
    st.caption(
        "Estimate a planning scenario from assumptions supplied by your team. These outputs are not measured "
        "results, a forecast, or ROI evidence from this dataset. Use verified conversion and finance inputs."
    )
    scenario_cols = st.columns(3)
    with scenario_cols[0]:
        monthly_opportunities = st.number_input(
            "Eligible monthly opportunities", min_value=0, value=0, step=500,
            help="For example, qualified visits or campaign exposures. Keep the unit consistent with the conversion rate.",
        )
        baseline_conversion_pct = st.number_input(
            "Baseline conversion rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1,
        )
    with scenario_cols[1]:
        expected_lift_pp = st.number_input(
            "Expected absolute lift (percentage points)", min_value=-100.0, max_value=100.0,
            value=0.0, step=0.1,
            help="Enter the assumed change in conversion rate, e.g. 0.5 means 2.0% to 2.5%.",
        )
        average_order_value = st.number_input(
            "Net revenue per conversion", min_value=0.0, value=0.0, step=100.0,
            help="Use a finance-approved value after refunds/discounts, in your chosen currency.",
        )
    with scenario_cols[2]:
        contribution_margin_pct = st.number_input(
            "Contribution margin (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0,
            help="Finance-approved share of net revenue remaining after variable costs.",
        )
        incremental_campaign_cost = st.number_input(
            "Incremental monthly campaign cost", min_value=0.0, value=0.0, step=100.0,
            help="Include only costs that change because of this campaign.",
        )
        currency_code = st.text_input(
            "Currency code (optional)", value="", max_chars=3, help="For example, INR or USD."
        )

    currency_code = currency_code.strip().upper()
    if currency_code and (len(currency_code) != 3 or not currency_code.isalpha()):
        st.error("Enter a three-letter currency code or leave it blank.")
        currency_code = ""
    currency_prefix = f"{currency_code} " if currency_code else ""

    scenario_conversion_pct = baseline_conversion_pct + expected_lift_pp
    if not 0 <= scenario_conversion_pct <= 100:
        st.error("Baseline plus assumed lift must be between 0% and 100%; adjust the scenario inputs.")
    else:
        impact = estimate_business_impact(
            monthly_opportunities=monthly_opportunities,
            baseline_conversion_rate=baseline_conversion_pct / 100,
            absolute_lift=expected_lift_pp / 100,
            net_revenue_per_conversion=average_order_value,
            contribution_margin=contribution_margin_pct / 100,
            incremental_campaign_cost=incremental_campaign_cost,
        )

        impact_cols = st.columns(4)
        impact_cols[0].metric(
            "Scenario conversion rate", f"{impact['scenario_conversion_rate'] * 100:.2f}%"
        )
        impact_cols[1].metric(
            "Incremental conversions / month", f"{impact['incremental_conversions']:,.1f}"
        )
        impact_cols[2].metric(
            "Incremental net revenue / month",
            f"{currency_prefix}{impact['incremental_net_revenue']:,.2f}",
        )
        impact_cols[3].metric(
            "Net contribution after campaign cost",
            f"{currency_prefix}{impact['net_contribution_after_cost']:,.2f}",
        )
        break_even_lift_pp = impact["break_even_absolute_lift"]
        if break_even_lift_pp is not None:
            st.caption(
                f"At these assumptions, break-even requires an absolute conversion lift of "
                f"{break_even_lift_pp * 100:.2f} percentage points. Use the same currency for revenue and cost inputs."
            )
        st.caption(
            "Scenario math: eligible opportunities × absolute conversion-rate lift = incremental conversions; "
            "then apply net revenue, contribution margin, and incremental campaign cost. A negative lift reduces "
            "the scenario value. Validate all assumptions and measure actual outcomes in a controlled test."
        )

with st.container(border=True):
    st.subheader("Conversion test sample planner")
    st.caption(
        "Approximate minimum sample size for a two-arm test of a binary conversion outcome. "
        "Use a verified baseline and a minimum useful lift agreed before launch."
    )
    sample_cols = st.columns(3)
    with sample_cols[0]:
        mde_pp = st.number_input(
            "Minimum detectable lift (percentage points)", min_value=0.0, max_value=100.0,
            value=0.0, step=0.1,
        )
    with sample_cols[1]:
        alpha_pct = st.number_input(
            "Two-sided significance level (%)", min_value=1.0, max_value=20.0,
            value=5.0, step=1.0,
        )
    with sample_cols[2]:
        power_pct = st.number_input(
            "Statistical power (%)", min_value=50.0, max_value=99.0,
            value=80.0, step=1.0,
        )

    baseline_probability = baseline_conversion_pct / 100
    lift_probability = mde_pp / 100
    test_probability = baseline_probability + lift_probability
    if not 0 < baseline_probability < 1:
        st.info("Enter a verified baseline conversion rate above 0% and below 100% to calculate sample size.")
    elif lift_probability <= 0 or test_probability >= 1:
        st.info("Enter a positive minimum detectable lift that keeps the test conversion rate below 100%.")
    else:
        sample_size = estimate_two_proportion_sample_size(
            baseline_rate=baseline_probability,
            minimum_detectable_lift=lift_probability,
            alpha=alpha_pct / 100,
            power=power_pct / 100,
        )
        st.metric(
            "Approximate eligible opportunities required",
            f"{sample_size['total']:,} total ({sample_size['per_arm']:,} per arm)",
        )
        st.caption(
            "Assumes independent binary outcomes, equal random allocation, a two-sided two-proportion normal approximation, "
            "no clustering, and no attrition. Repeated users, post-level clustering, multiple primary outcomes, or "
            "noncompliance require a design-specific power calculation."
        )

    with st.expander("Data required to make stronger business decisions"):
        st.markdown(
            """
            Collect a stable post ID, account ID, source/export timestamp, publication timestamp, caption,
            paid/organic flag, spend, follower count at publication, metric definitions, link clicks,
            and consented conversion and sales attribution. Document who owns the source and how records
            were sampled. Add demographic fields only when there is a valid business purpose and approved use.
            """
        )

    st.warning(
        "This dataset has no revenue, cost, or attributed conversion data, so actual revenue and ROI cannot be measured. "
        "The scenario calculator uses only user-entered assumptions; listed action rates are aggregate proxies, "
        "not person-level conversion measures."
    )

with st.container(border=True):
    st.subheader("Measure observed business impact")
    st.caption(
        "Upload a reconciled source export using the documented row grain, attribution rule, and finance definitions. "
        "This file must link post-level performance to deduplicated conversion, revenue, cost, and currency values."
    )
    template_path = ROOT / "data" / "business_impact_attribution_template.csv"
    st.download_button(
        "Download blank attribution CSV template",
        data=template_path.read_bytes(),
        file_name="business_impact_attribution_template.csv",
        mime="text/csv",
        key="download_business_impact_template",
    )
    attribution_upload = st.file_uploader(
        "Upload validated per-post attribution data (CSV)",
        type=["csv"],
        key="business_impact_attribution_upload",
        help="Use one row per unique post, one attribution method/window, and one currency per upload.",
    )
    if attribution_upload is not None:
        try:
            attribution_data = pd.read_csv(attribution_upload)
            impact_validation = validate_attribution_data(attribution_data)
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(f"Could not read or validate the uploaded CSV: {error}")
        else:
            if not impact_validation["valid"]:
                st.error("The attribution upload needs correction before analysis.")
                for message in impact_validation["errors"]:
                    st.markdown(f"- {message}")
            else:
                currency = impact_validation["currency_code"]
                st.success(
                    f"Validated {impact_validation['rows']:,} rows; "
                    f"{impact_validation['attribution_method']} attribution, "
                    f"{impact_validation['attribution_window_days']:g}-day window, {currency}."
                )
                breakdown_dimension = st.selectbox(
                    "Observed impact breakdown",
                    options=["post_type", "campaign_type"],
                    format_func=lambda value: "Post type" if value == "post_type" else "Campaign type",
                    key="business_impact_breakdown",
                )
                impact_summary = aggregate_business_impact(attribution_data, breakdown_dimension)
                total_revenue = impact_summary["attributed_net_revenue"].sum()
                total_spend = impact_summary["paid_media_cost"].sum()
                total_net_contribution = impact_summary["net_contribution"].sum()
                impact_kpis = st.columns(4)
                impact_kpis[0].metric(
                    "Attributed conversions", f"{impact_summary['attributed_conversions'].sum():,.0f}"
                )
                impact_kpis[1].metric("Attributed net revenue", f"{currency} {total_revenue:,.2f}")
                impact_kpis[2].metric("Paid media cost", f"{currency} {total_spend:,.2f}")
                impact_kpis[3].metric(
                    "Net contribution after media", f"{currency} {total_net_contribution:,.2f}"
                )
                impact_display = impact_summary.rename(
                    columns={
                        breakdown_dimension: "Category",
                        "eligible_opportunities": "Eligible opportunities",
                        "attributed_conversions": "Attributed conversions",
                        "attributed_net_revenue": "Net revenue",
                        "variable_cost": "Variable cost",
                        "paid_media_cost": "Paid media cost",
                        "contribution_before_paid_media": "Contribution before media",
                        "net_contribution": "Net contribution",
                        "conversion_rate": "Conversion rate",
                        "customer_acquisition_cost": "Acquisition cost",
                        "net_roas": "Net ROAS",
                        "roi": "ROI",
                    }
                )
                st.dataframe(
                    impact_display[
                        [
                            "Category",
                            "records",
                            "Eligible opportunities",
                            "Attributed conversions",
                            "Conversion rate",
                            "Net revenue",
                            "Variable cost",
                            "Paid media cost",
                            "Contribution before media",
                            "Net contribution",
                            "Acquisition cost",
                            "Net ROAS",
                            "ROI",
                        ]
                    ].style.format(
                        {
                            "records": "{:,.0f}",
                            "Eligible opportunities": "{:,.0f}",
                            "Attributed conversions": "{:,.0f}",
                            "Conversion rate": "{:.2%}",
                            "Net revenue": f"{currency} {{:,.2f}}",
                            "Variable cost": f"{currency} {{:,.2f}}",
                            "Paid media cost": f"{currency} {{:,.2f}}",
                            "Contribution before media": f"{currency} {{:,.2f}}",
                            "Net contribution": f"{currency} {{:,.2f}}",
                            "Acquisition cost": f"{currency} {{:,.2f}}",
                            "Net ROAS": "{:.2f}x",
                            "ROI": "{:.1%}",
                        },
                        na_rep="—",
                    ),
                    width="stretch",
                    hide_index=True,
                )
                st.caption(
                    "Observed attributed metrics describe this uploaded export. Attribution is not incrementality: "
                    "use a verified randomized control to support causal business-impact claims."
                )

                if impact_validation["experiment_fields_available"]:
                    portfolio_confidence_pct = (
                        1 - portfolio["testwise_alpha_bonferroni"]
                    ) * 100
                    confidence_level_pct = st.number_input(
                        "Confidence level for preregistered arm intervals (%)",
                        min_value=90.0,
                        max_value=99.9,
                        value=round(portfolio_confidence_pct, 2),
                        step=0.01,
                        help="The assumed three-test portfolio uses 98.33% intervals to control family-wise error at 5%. Set this to the level recorded in the actual experiment preregistration.",
                        key="business_impact_arm_confidence_level",
                    )
                    randomization_verified = st.checkbox(
                        "I verified a preregistered random assignment and consistent outcome measurement for these arms.",
                        value=False,
                        key="business_impact_randomization_verified",
                    )
                    if randomization_verified:
                        try:
                            experiment_result = compare_randomized_arms(
                                attribution_data,
                                confidence_level=confidence_level_pct / 100,
                            )
                        except ValueError as error:
                            st.error(str(error))
                        else:
                            arm_kpis = st.columns(4)
                            arm_kpis[0].metric(
                                "Treatment − control conversion rate",
                                f"{experiment_result['treatment_minus_control_conversion_rate_pp']:+.2f} pp",
                                help=(
                                    f"{experiment_result['confidence_level']:.2%} unit-bootstrap interval: "
                                    f"[{experiment_result['conversion_rate_difference_ci_low_pp']:+.2f}, "
                                    f"{experiment_result['conversion_rate_difference_ci_high_pp']:+.2f}] pp"
                                ),
                            )
                            arm_kpis[1].metric(
                                "Treatment − control net contribution / unit",
                                f"{currency} {experiment_result['net_contribution_difference_per_unit']:+,.2f}",
                                help=(
                                    f"{experiment_result['confidence_level']:.2%} unit-bootstrap interval: {currency} "
                                    f"[{experiment_result['net_contribution_difference_ci_low']:+,.2f}, "
                                    f"{experiment_result['net_contribution_difference_ci_high']:+,.2f}]"
                                ),
                            )
                            arm_kpis[2].metric("Control units", f"{experiment_result['control_units']:,}")
                            arm_kpis[3].metric("Treatment units", f"{experiment_result['treatment_units']:,}")
                            st.caption(experiment_result["interpretation"])
                    else:
                        st.info(
                            "Arm results are not interpreted as causal until the randomization protocol and execution are verified."
                        )
                else:
                    st.info(
                        "No randomized control/treatment fields were supplied. The observed attribution table is descriptive; "
                        "it cannot estimate incremental lift."
                    )

                st.download_button(
                    "Download calculated business impact table",
                    data=impact_summary.to_csv(index=False).encode("utf-8"),
                    file_name="observed_business_impact_by_category.csv",
                    mime="text/csv",
                    key="download_calculated_business_impact",
                )

st.caption(
    "The selected-scope baseline is the weighted rate across all currently filtered records; it is a descriptive reference, not an independent benchmark. Format comparisons use the current supplied file and filters. Hashtag categories overlap; summed reach is not unique reach."
)
