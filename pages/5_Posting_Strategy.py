from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent if Path(__file__).parent.name == "pages" else Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize

st.set_page_config(
    page_title="SUGAR | Posting Strategy",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

context = initialize("Posting Strategy")
globals().update(context)

# Page heading uses the shared SUGAR theme and remains consistent with other pages.
st.markdown(
    """
    <div class="sugar-page-heading">
      <div class="sugar-eyebrow"><span class="sugar-mark">S</span> SUGAR COSMETICS
      <span class="sugar-slash">/</span> INSTAGRAM PERFORMANCE ANALYTICS</div>
      <h1>Posting Strategy</h1>
      <p>Understand posting cadence and the days associated with stronger engagement.</p>
      <div class="sugar-heading-accent"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .sugar-takeaway-box {
        background: #351f2d;
        border-left: 3px solid #f05a98;
        border-radius: 0 9px 9px 0;
        padding: 13px 16px 14px 15px;
        margin: 12px 0 20px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.10);
    }
    .sugar-takeaway-label {
        color: #ff8fba;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.045em;
        margin-bottom: 4px;
    }
    .sugar-takeaway-text {
        color: #fff7fb;
        font-size: 0.94rem;
        line-height: 1.55;
        font-weight: 450;
    }
    .sugar-takeaway-text strong { color: #ffffff; font-weight: 750; }
    </style>
    """,
    unsafe_allow_html=True,
)

page_kpis("Posting Strategy", f)

# Monthly posting cadence
st.markdown("## Posting cadence")
monthly = (
    f.assign(month=f["post_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .size()
    .rename(columns={"size": "records"})
    .sort_values("month")
)

if not monthly.empty:
    fig_monthly = px.area(
        monthly,
        x="month",
        y="records",
        markers=True,
        title="Posting volume by month",
        labels={"month": "Month", "records": "Records"},
        color_discrete_sequence=["#e84f87"],
    )
    fig_monthly.update_traces(
        line=dict(color="#e84f87", width=3),
        fillcolor="rgba(232,79,135,0.18)",
        marker=dict(size=8, color="#8e476b", line=dict(color="#fff0f6", width=1.5)),
        hovertemplate="<b>%{x|%b %Y}</b><br>Records: %{y:,}<extra></extra>",
    )
    fig_monthly.update_layout(
        template="sugar",
        title=dict(text="Posting volume by month", x=0.02, xanchor="left"),
        margin=dict(l=15, r=20, t=65, b=15),
        hovermode="x unified",
    )
    st.plotly_chart(fig_monthly, width="stretch")
    peak_month = monthly.loc[monthly["records"].idxmax()]
    low_month = monthly.loc[monthly["records"].idxmin()]
    takeaway = (
        f"Posting volume peaked in <strong>{peak_month['month']:%B %Y}</strong> "
        f"({peak_month['records']:,} records) and was lowest in "
        f"<strong>{low_month['month']:%B %Y}</strong> ({low_month['records']:,} records). "
        "Use this as a cadence observation, not proof that posting volume caused engagement changes."
    )
    st.markdown(
        f"""<div class="sugar-takeaway-box">
          <div class="sugar-takeaway-label">KEY TAKEAWAY</div>
          <div class="sugar-takeaway-text">{takeaway}</div>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.info("No monthly posting data is available for the selected filters.")

st.divider()

# Weekday engagement
weekdays = weekday_table(f).copy()
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

if not weekdays.empty:
    weekdays["weekday"] = pd.Categorical(
        weekdays["weekday"], categories=weekday_order, ordered=True
    )
    weekdays = weekdays.sort_values("weekday")
    weekdays["weighted_engagement_rate"] = pd.to_numeric(
        weekdays["weighted_engagement_rate"], errors="coerce"
    )
    chart_weekdays = weekdays.dropna(subset=["weighted_engagement_rate"]).copy()

    if not chart_weekdays.empty:
        best_day = chart_weekdays.loc[chart_weekdays["weighted_engagement_rate"].idxmax()]
        worst_day = chart_weekdays.loc[chart_weekdays["weighted_engagement_rate"].idxmin()]

        fig_weekdays = px.bar(
            chart_weekdays,
            x="weekday",
            y="weighted_engagement_rate",
            title="Weighted engagement rate by weekday",
            labels={
                "weekday": "Day of week",
                "weighted_engagement_rate": "Weighted engagement rate",
            },
            color="weekday",
            color_discrete_sequence=[
                "#e84f87", "#8e476b", "#f29abb", "#c85b89",
                "#a96a91", "#e9b1c8", "#70405c",
            ],
            category_orders={"weekday": weekday_order},
        )
        fig_weekdays.update_traces(
            marker_line_color="#fff0f6",
            marker_line_width=1.2,
            opacity=0.96,
            hovertemplate="<b>%{x}</b><br>Weighted engagement rate: %{y:.2%}<extra></extra>",
        )
        fig_weekdays.update_layout(
            template="sugar",
            title=dict(text="Weighted engagement rate by weekday", x=0.02, xanchor="left"),
            showlegend=False,
            yaxis_tickformat=".1%",
            margin=dict(l=15, r=20, t=65, b=15),
        )
        st.plotly_chart(fig_weekdays, width="stretch")
        takeaway = (
            f"<strong>{best_day['weekday']}</strong> has the highest weighted engagement rate "
            f"({best_day['weighted_engagement_rate']:.2%}) in the selected data, while "
            f"<strong>{worst_day['weekday']}</strong> has the lowest "
            f"({worst_day['weighted_engagement_rate']:.2%}). "
            "Treat this as an observed association; test weekday choices before changing the publishing calendar."
        )
        st.markdown(
            f"""<div class="sugar-takeaway-box">
              <div class="sugar-takeaway-label">KEY TAKEAWAY</div>
              <div class="sugar-takeaway-text">{takeaway}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.info("Weekday engagement rates are unavailable for the selected filters.")

st.markdown("### Weekday performance details")
display_weekdays = weekdays.copy()
if "weighted_engagement_rate" in display_weekdays.columns:
    display_weekdays["weighted_engagement_rate"] = display_weekdays[
        "weighted_engagement_rate"
    ].map(lambda value: f"{value:.2%}" if pd.notna(value) else "—")
st.dataframe(display_weekdays, width="stretch", hide_index=True)

st.info(
    "The dataset contains post dates but no posting-time field. It can support weekday analysis, "
    "but it cannot establish the best hour of day to publish."
)

st.divider()
st.caption(
    "SUGAR Cosmetics Instagram Performance Analytics · Results reflect the supplied dataset "
    "and active global filters. Dataset provenance is not independently verified."
)
