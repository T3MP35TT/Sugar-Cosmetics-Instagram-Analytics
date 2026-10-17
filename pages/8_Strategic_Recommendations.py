from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize


context = initialize("Strategic Recommendations")
globals().update(context)

page_kpis("Strategic Recommendations", f)
st.subheader("Use these comparisons to plan a test")
st.caption(
    "The supplied records support descriptive comparisons. They do not identify a causal winner. "
    "The likely upstream file source is documented in DATA_PROVENANCE.md. Confirm collection method and row grain before treating this as brand performance."
)

if f.empty:
    st.warning("No records match the current data selection. Widen the date range or filters to compare formats.")
else:
    grouped = (
        f.groupby("post_type", dropna=False)
        .agg(
            records=("post_type", "size"),
            reach=("reach", "sum"),
            engagements=("total_engagements", "sum"),
            mean_record_rate=("engagement_rate", "mean"),
            saves=("saves", "sum"),
            shares=("shares", "sum"),
            visits=("profile_visits", "sum"),
            follows=("follows", "sum"),
        )
        .reset_index()
    )
    grouped["weighted_engagement_rate"] = (
        grouped["engagements"] / grouped["reach"].where(grouped["reach"] > 0)
    )
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
                "Saves / reach proxy",
                "Shares / reach proxy",
                "Follows / visits proxy",
            ]
        ].style.format(
            {
                "Summed reach": "{:,.0f}",
                "Mean record engagement rate": "{:.2%}",
                "Weighted engagement rate": "{:.2%}",
                "Saves / reach proxy": "{:.2%}",
                "Shares / reach proxy": "{:.2%}",
                "Follows / visits proxy": "{:.2%}",
            },
            na_rep="—",
        ),
        width="stretch",
        hide_index=True,
    )

st.subheader("Experiment brief")
st.markdown(
    """
| Decision item | Specify before launch |
|---|---|
| Hypothesis | Choose one audience and campaign goal; state why the tested format should change the outcome. |
| Treatment and comparison | Randomly assign eligible content opportunities where practical. Keep campaign objective, paid support, and measurement window comparable. |
| Primary outcome | Select one: weighted engagement rate, saves per reach, shares per reach, or a validated attributed conversion rate. |
| Guardrails | Track reach, negative feedback, spend, and any brand safety measure relevant to the campaign. |
| Baseline and target | Use validated historical data and agree the minimum useful change with the marketing owner. Do not use this unverified file as the baseline. |
| Sample and stopping rule | Set the required sample size and end date before launch. Avoid stopping early because interim results look favorable. |
| Decision | Report the estimate, uncertainty, limitations, and whether the agreed threshold was met. Follow up with a replication when the result is uncertain. |
"""
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
    "No revenue or ROI estimate is supportable from the current fields. The listed action rates are "
    "aggregate proxies, not person-level conversion measures."
)
st.caption(
    "Format comparisons use the current supplied file and filters. Hashtag categories overlap; "
    "summed reach is not unique reach."
)
