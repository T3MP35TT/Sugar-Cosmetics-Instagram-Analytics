from pathlib import Path
import sys
import html

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent if Path(__file__).parent.name == "pages" else Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize
from analytics import hashtag_table

st.set_page_config(
    page_title="SUGAR | Hashtag Intelligence",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

context = initialize("Hashtag Intelligence")
globals().update(context)

PINK = "#F05291"
DARK_PINK = "#6E3157"
PALE_PINK = "#F6A6C1"


def card_title(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def takeaway(message):
    st.markdown(
        f"""
        <div style="margin:.55rem 0 .15rem;padding:.8rem 1rem;
        border:1px solid rgba(240,82,145,.35);border-left:4px solid {PINK};
        border-radius:10px;background:rgba(240,82,145,.08);line-height:1.55;">
        <strong style="color:{PALE_PINK};">KEY TAKEAWAY</strong><br>
        {html.escape(str(message))}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Preparing hashtag analysis…", max_entries=8)
def build_hashtag_summary(data):
    # Cached per filtered dataframe; repeated Streamlit reruns reuse this aggregation.
    return hashtag_table(data).copy()


st.caption("Explore hashtag usage, observed engagement, and performance rankings. A post can contain multiple hashtags, so totals overlap.")

ht = build_hashtag_summary(f)

if ht.empty:
    with st.container(border=True):
        card_title("Hashtag overview")
        st.info("No hashtags were found in the currently selected records.")
else:
    # Prepare derived fields once, then reuse them throughout the page.
    ht["avg_engagements_per_record"] = ht["engagements"] / ht["records"].replace(0, pd.NA)
    ht = ht.sort_values(["weighted_engagement_rate", "records"], ascending=[False, False]).reset_index(drop=True)
    popular = ht.loc[ht["records"].idxmax()]
    min_support = min(10, max(2, int(ht["records"].median())))
    supported = ht.loc[ht["records"] >= min_support]
    besttag = (supported if not supported.empty else ht).iloc[0]

    with st.container(border=True):
        card_title("Hashtag performance KPIs", "A quick snapshot of hashtag coverage and observed performance.")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Unique hashtags", f"{ht['hashtag'].nunique():,}")
        k2.metric("Hashtag uses", f"{ht['records'].sum():,.0f}")
        k3.metric("Most-used hashtag", str(popular["hashtag"]))
        k4.metric("Highest-rate hashtag*", str(besttag["hashtag"]))
        takeaway(
            f"{popular['hashtag']} is the most frequently used hashtag ({int(popular['records']):,} records). "
            f"{besttag['hashtag']} has the highest observed weighted engagement rate among hashtags meeting the support threshold "
            f"of {min_support} records, where available."
        )

    with st.container(border=True):
        card_title("Hashtag filters", "Limit the minimum number of records and choose the ranking metric.")
        c1, c2, c3 = st.columns([1, 1.7, 1.2])
        max_usage = max(1, int(ht["records"].max()))
        min_usage = c1.number_input(
            "Minimum records per hashtag", min_value=1, max_value=max_usage,
            value=1, step=1, key="hashtag_page_min_usage",
        )
        tags = sorted(ht["hashtag"].dropna().astype(str).unique().tolist())
        selected = c2.multiselect(
            "Hashtags to include", options=tags, default=tags,
            key="hashtag_page_select",
        )
        rank_metric = c3.selectbox(
            "Rank by",
            ["Weighted engagement rate", "Usage count", "Total engagements", "Total saves"],
            key="hashtag_page_rank",
        )

    filtered = ht.loc[(ht["records"] >= min_usage) & ht["hashtag"].isin(selected)].copy()

    if filtered.empty:
        with st.container(border=True):
            card_title("Filtered hashtag results")
            st.warning("No hashtags match these filters. Lower the minimum record count or select more hashtags.")
    else:
        with st.container(border=True):
            card_title(
                "Hashtags ranked by weighted engagement rate",
                "A rate ranking can favor hashtags with a small sample; check record count and reach.",
            )
            rate_top = filtered.nlargest(15, "weighted_engagement_rate").sort_values("weighted_engagement_rate")
            fig = px.bar(
                rate_top,
                x="weighted_engagement_rate",
                y="hashtag",
                orientation="h",
                text=rate_top["weighted_engagement_rate"].map(
                    lambda value: f"{value:.1%}" if pd.notna(value) else "—"
                ),
                color="weighted_engagement_rate",
                color_continuous_scale=["#FADCE8", PINK, DARK_PINK],
                labels={
                    "weighted_engagement_rate": "Weighted engagement rate",
                    "hashtag": "Hashtag",
                },
                custom_data=["records", "reach", "engagements"],
            )
            fig.update_traces(
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b><br>Weighted engagement rate: %{x:.2%}"
                    "<br>Records: %{customdata[0]:,.0f}"
                    "<br>Summed post reach: %{customdata[1]:,.0f}"
                    "<br>Total engagements: %{customdata[2]:,.0f}<extra></extra>"
                ),
                cliponaxis=False,
            )
            fig.update_layout(
                template="sugar",
                coloraxis_showscale=False,
                xaxis_tickformat=".0%",
                margin=dict(l=10, r=45, t=15, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            leader = filtered.loc[filtered["weighted_engagement_rate"].idxmax()]
            rate = leader["weighted_engagement_rate"]
            if pd.notna(rate):
                takeaway(
                    f"{leader['hashtag']} leads the current selection at {rate:.2%} across "
                    f"{int(leader['records']):,} records. Check its sample size before treating it as a reliable winner."
                )
            else:
                takeaway("The selected hashtags do not have a calculable weighted engagement rate.")

        with st.container(border=True):
            card_title(
                "Hashtag usage versus engagement rate",
                "Each bubble is a hashtag; size represents summed post-level reach, not unique people.",
            )
            fig = px.scatter(
                filtered,
                x="records",
                y="weighted_engagement_rate",
                size="reach",
                color="engagements",
                hover_name="hashtag",
                size_max=35,
                color_continuous_scale=[PALE_PINK, PINK, DARK_PINK],
                labels={
                    "records": "Records using hashtag",
                    "weighted_engagement_rate": "Weighted engagement rate",
                    "engagements": "Total engagements",
                    "reach": "Summed post reach",
                },
                custom_data=["reach", "engagements"],
            )
            fig.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b><br>Records: %{x:,.0f}"
                    "<br>Weighted engagement rate: %{y:.2%}"
                    "<br>Summed post reach: %{customdata[0]:,.0f}"
                    "<br>Total engagements: %{customdata[1]:,.0f}<extra></extra>"
                )
            )
            fig.update_layout(
                template="sugar",
                xaxis_title="Records using hashtag",
                yaxis_tickformat=".0%",
                margin=dict(l=10, r=10, t=15, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            high_use = filtered.loc[filtered["records"].idxmax()]
            high_rate = filtered.loc[filtered["weighted_engagement_rate"].idxmax()]
            takeaway(
                f"{high_use['hashtag']} has the greatest usage in this selection, while "
                f"{high_rate['hashtag']} has the highest observed rate. Usage and rate measure different outcomes."
            )

        metric_col = {
            "Weighted engagement rate": "weighted_engagement_rate",
            "Usage count": "records",
            "Total engagements": "engagements",
            "Total saves": "saves",
        }[rank_metric]

        with st.container(border=True):
            card_title("Hashtag leaderboard", "Sort and export the selected hashtags using the metric that matches your question.")
            display = filtered.sort_values(metric_col, ascending=False)[
                [
                    "hashtag", "records", "reach", "engagements",
                    "weighted_engagement_rate", "avg_engagements_per_record",
                    "likes", "comments", "shares", "saves", "follows",
                ]
            ].rename(columns={
                "hashtag": "Hashtag",
                "records": "Records",
                "reach": "Summed post reach",
                "engagements": "Total engagements",
                "weighted_engagement_rate": "Weighted engagement rate",
                "avg_engagements_per_record": "Avg engagements / record",
                "likes": "Likes",
                "comments": "Comments",
                "shares": "Shares",
                "saves": "Saves",
                "follows": "Follows",
            })
            st.dataframe(
                display.style.format(
                    {
                        "Weighted engagement rate": "{:.2%}",
                        "Avg engagements / record": "{:,.1f}",
                        "Summed post reach": "{:,.0f}",
                        "Total engagements": "{:,.0f}",
                    },
                    na_rep="—",
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "Download hashtag leaderboard (CSV)",
                data=display.to_csv(index=False).encode("utf-8"),
                file_name="sugar_hashtag_leaderboard.csv",
                mime="text/csv",
            )
            takeaway(
                f"The leaderboard is currently ranked by {rank_metric.lower()}. "
                "High engagement rate, high usage and high total contribution are different outcomes."
            )

with st.container(border=True):
    card_title("How to interpret hashtag results")
    st.markdown(
        "- Hashtag totals overlap because a post can contain multiple hashtags.\n"
        "- Summed post reach is not unique reach.\n"
        "- Observed associations do not prove that a hashtag caused engagement."
    )

st.caption("Sugar Cosmetics Instagram Performance Analytics · Results are based on the selected supplied dataset.")
