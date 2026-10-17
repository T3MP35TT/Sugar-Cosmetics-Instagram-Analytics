from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent if Path(__file__).parent.name == "pages" else Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize

st.set_page_config(
    page_title="SUGAR | Instagram Intelligence",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

context = initialize("Executive Overview")
globals().update(context)

# SUGAR-inspired chart palette: vivid pink, plum, rose, berry and soft blush.
CHART_COLORS = [
    "#F05291",
    "#9B4D78",
    "#F6A6C1",
    "#C43D73",
    "#D77AA5",
    "#6E3157",
    "#F7C6D8",
    "#B65A88",
]

PLOT_LAYOUT = dict(
    template="sugar",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,248,251,0.04)",
    font=dict(family="Arial, sans-serif", color="#F9EAF1", size=12),
    title=dict(font=dict(size=17, color="#FFF4F8"), x=0.02, xanchor="left"),
    margin=dict(l=18, r=18, t=62, b=22),
    colorway=CHART_COLORS,
    hoverlabel=dict(bgcolor="#2A1A27", bordercolor="#F05291", font_color="#FFFFFF"),
    xaxis=dict(showgrid=False, zeroline=False, linecolor="#765568", tickfont=dict(color="#EBD8E3")),
    yaxis=dict(showgrid=True, gridcolor="rgba(230,190,210,0.16)", zeroline=False, linecolor="#765568",
               tickfont=dict(color="#EBD8E3")),
)


def style_figure(fig, *, percent_axis=False):
    fig.update_layout(**PLOT_LAYOUT)
    if percent_axis:
        fig.update_yaxes(tickformat=".1%")
    fig.update_traces(
        hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        line=dict(width=3),
        marker=dict(size=8, line=dict(width=1.5, color="#FFF4F8")),
    )
    return fig


def compact_number(value):
    """Format large KPI values so they fit inside executive dashboard cards."""
    if value is None or pd.isna(value):
        return "—"
    value = float(value)
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if magnitude >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if magnitude >= 100_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:,.0f}"


def takeaway(text):
    st.markdown(
        f"""
        <div style="
            margin-top:-0.35rem;
            margin-bottom:1.1rem;
            padding:0.75rem 0.9rem;
            border-left:4px solid #F05291;
            border-radius:0 9px 9px 0;
            background:rgba(240,82,145,0.10);
            color:#F8EAF1;
            font-size:0.92rem;
            line-height:1.5;">
            <span style="font-weight:700;color:#F6A6C1;">KEY TAKEAWAY</span><br>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )



st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        min-height: 88px;
        padding: 12px 14px;
        border: 1px solid rgba(240, 82, 145, 0.28);
        border-top: 2px solid #9B4D78;
        border-radius: 12px;
        background: rgba(255, 248, 251, 0.035);
        margin-bottom: 10px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: clamp(1.25rem, 1.55vw, 1.85rem);
        line-height: 1.2;
        overflow-wrap: anywhere;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Executive filters: all KPIs and visuals below respond to the same selection.
source_data = f.copy()
source_data["post_date"] = pd.to_datetime(source_data["post_date"], errors="coerce", format="mixed")
with st.container(border=True):
    st.markdown("### Report filters")
    filter_cols = st.columns(4)
    valid_dates = source_data["post_date"].dropna()
    if not valid_dates.empty:
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
        selected_dates = filter_cols[0].date_input(
            "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
            key="exec_v20_date_range",
        )
    else:
        selected_dates = ()
    post_types = sorted(source_data["post_type"].dropna().astype(str).unique()) if "post_type" in source_data else []
    selected_types = filter_cols[1].multiselect("Post type", post_types, default=post_types, key="exec_v20_post_type")
    campaigns_available = sorted(source_data["campaign_type"].dropna().astype(str).unique()) if "campaign_type" in source_data else []
    selected_campaigns = filter_cols[2].multiselect("Campaign", campaigns_available, default=campaigns_available, key="exec_v20_campaign")
    sources_available = sorted(source_data["engagement_source"].dropna().astype(str).unique()) if "engagement_source" in source_data else []
    selected_sources = filter_cols[3].multiselect("Engagement source", sources_available, default=sources_available, key="exec_v20_source") if sources_available else []

f = source_data.copy()
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    f = f[f["post_date"].dt.date.between(selected_dates[0], selected_dates[1])]
if "post_type" in f.columns:
    f = f[f["post_type"].astype(str).isin(selected_types)]
if "campaign_type" in f.columns:
    f = f[f["campaign_type"].astype(str).isin(selected_campaigns)]
if sources_available and "engagement_source" in f.columns:
    f = f[f["engagement_source"].astype(str).isin(selected_sources)]

if f.empty:
    st.warning("No records match these filters. Widen the date range or select more values.")
    st.stop()

valid_date_count = int(f["post_date"].notna().sum())
start_date = f["post_date"].min()
end_date = f["post_date"].max()
with st.container(border=True):
    st.markdown("**Measurement confidence**")
    st.write(
        f"Current selection: **{len(f):,} records**, with **{valid_date_count:,} valid dates**. "
        + (f"Date coverage: **{start_date:%d %b %Y} – {end_date:%d %b %Y}**. " if pd.notna(start_date) and pd.notna(end_date) else "Date coverage is unavailable. ")
        + "The source does not establish provenance or provide a unique post identifier. "
        "Treat counts as records, not confirmed unique posts; category comparisons are descriptive, not causal."
    )

kpis(f)

st.subheader("Performance over time")
# Build monthly metrics from valid dates only. Rates are weighted from totals,
# rather than averaging post-level percentages.
overview_data = f.copy()
overview_data["post_date"] = pd.to_datetime(
    overview_data["post_date"], errors="coerce", format="mixed"
)
for numeric_col in ["reach", "total_engagements", "impressions", "follows", "engagement_rate"]:
    if numeric_col in overview_data.columns:
        overview_data[numeric_col] = pd.to_numeric(
            overview_data[numeric_col], errors="coerce"
        )

monthly_source = overview_data.dropna(subset=["post_date"]).copy()
monthly = (
    monthly_source.assign(month=monthly_source["post_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .agg(
        posts=("post_date", "size"),
        reach=("reach", lambda s: s.sum(min_count=1)),
        engagements=("total_engagements", lambda s: s.sum(min_count=1)),
        impressions=("impressions", lambda s: s.sum(min_count=1)),
    )
    .rename(columns={"month": "post_date"})
)
monthly["engagement_rate"] = (
    monthly["engagements"] / monthly["reach"].where(monthly["reach"] > 0)
)

left, right = st.columns(2)

with left:
    posting_fig = px.area(
        monthly,
        x="post_date",
        y="posts",
        title="Record volume by month",
        labels={"post_date": "Month", "posts": "Records"},
        color_discrete_sequence=[CHART_COLORS[0]],
        markers=True,
    )
    posting_fig.update_traces(
        fill="tozeroy",
        fillcolor="rgba(240,82,145,0.18)",
        line=dict(color=CHART_COLORS[0], width=3),
        marker=dict(size=8, color=CHART_COLORS[0], line=dict(width=1.5, color="#FFF4F8")),
        hovertemplate="<b>%{x|%b %Y}</b><br>Records: %{y:,.0f}<extra></extra>",
    )
    posting_fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(posting_fig, width="stretch")
    if not monthly.empty:
        peak = monthly.loc[monthly["posts"].idxmax()]
        lowest = monthly.loc[monthly["posts"].idxmin()]
        takeaway(
            f"Record volume peaked in <b>{peak['post_date']:%b %Y}</b> "
            f"({peak['posts']:,.0f} records) and was lowest in "
            f"<b>{lowest['post_date']:%b %Y}</b> ({lowest['posts']:,.0f}). "
            "These are record counts, not verified publishing counts; the dataset has no unique post ID."
        )
    else:
        takeaway("There are no monthly records in the current filter selection.")

with right:
    rate_fig = px.line(
        monthly,
        x="post_date",
        y="engagement_rate",
        title="Weighted engagement rate by month",
        labels={"post_date": "Month", "engagement_rate": "Engagement rate"},
        color_discrete_sequence=[CHART_COLORS[1]],
        markers=True,
    )
    rate_fig.update_traces(
        line=dict(color=CHART_COLORS[1], width=3),
        marker=dict(size=9, color=CHART_COLORS[2], line=dict(width=2, color=CHART_COLORS[1])),
        hovertemplate="<b>%{x|%b %Y}</b><br>Weighted engagement rate: %{y:.2%}<extra></extra>",
    )
    rate_fig.update_layout(**PLOT_LAYOUT)
    valid_rates = monthly.dropna(subset=["engagement_rate"])
    # Use a zero baseline for a fair visual comparison; do not magnify small
    # percentage-point changes with a truncated axis.
    rate_fig.update_yaxes(
        tickformat=".2%",
        title="Weighted engagement rate (zero baseline)",
        rangemode="tozero",
    )
    st.plotly_chart(rate_fig, width="stretch")
    if not valid_rates.empty:
        peak = valid_rates.loc[valid_rates["engagement_rate"].idxmax()]
        lowest = valid_rates.loc[valid_rates["engagement_rate"].idxmin()]
        rate_gap_pp = (float(peak["engagement_rate"]) - float(lowest["engagement_rate"])) * 100
        takeaway(
            f"Weighted engagement rate was highest in <b>{peak['post_date']:%b %Y}</b> "
            f"({peak['engagement_rate']:.2%}) and lowest in "
            f"<b>{lowest['post_date']:%b %Y}</b> ({lowest['engagement_rate']:.2%}), "
            f"a difference of <b>{rate_gap_pp:.2f} percentage points</b>. "
            "The chart uses a zoomed vertical scale; compare content mix and record counts "
            "before treating this difference as strategically meaningful."
        )
    else:
        takeaway("Engagement rate cannot be calculated for the selected data because reach is zero or unavailable.")

st.subheader("What stands out in the selected data")
comparison_data = overview_data.copy()
comparison_data["post_type"] = comparison_data["post_type"].fillna("Unknown").astype(str)
comparison_data["campaign_type"] = comparison_data["campaign_type"].fillna("Unknown").astype(str)

types = (
    comparison_data.groupby("post_type", dropna=False)
    .agg(
        posts=("post_type", "size"),
        reach=("reach", lambda s: s.sum(min_count=1)),
        engagements=("total_engagements", lambda s: s.sum(min_count=1)),
        avg_engagement_rate=("engagement_rate", "mean"),
        follows=("follows", lambda s: s.sum(min_count=1)),
    )
    .reset_index()
)
types["weighted_engagement_rate"] = (
    types["engagements"] / types["reach"].where(types["reach"] > 0)
)
types = types.sort_values("weighted_engagement_rate", ascending=False, na_position="last")

col1, col2 = st.columns(2)

with col1:
    chart_area, metric_area = st.columns([2.25, 1], gap="small")
    with chart_area:
        type_fig = px.bar(
            types,
            x="post_type",
            y="weighted_engagement_rate",
            title="Weighted engagement rate by post type",
            labels={"post_type": "Post type", "weighted_engagement_rate": "Weighted engagement rate"},
            color="post_type",
            color_discrete_sequence=CHART_COLORS,
            text=types["weighted_engagement_rate"].map(lambda value: f"{value:.1%}" if pd.notna(value) else "—"),
        )
        type_fig.update_traces(
            textposition="outside", cliponaxis=False,
            marker_line_color="rgba(255,244,248,0.55)", marker_line_width=1,
            customdata=types[["posts", "reach", "engagements"]].to_numpy(),
            hovertemplate=("<b>%{x}</b><br>Weighted engagement rate: %{y:.2%}"
                           "<br>Records: %{customdata[0]:,.0f}"
                           "<br>Summed post reach: %{customdata[1]:,.0f}"
                           "<br>Engagements: %{customdata[2]:,.0f}<extra></extra>"),
        )
        type_fig.update_layout(**PLOT_LAYOUT, showlegend=False, height=490)
        type_fig.update_yaxes(tickformat=".1%", rangemode="tozero")
        st.plotly_chart(type_fig, width="stretch")
    with metric_area:
        st.markdown("**Post type at a glance**")
        st.metric("Formats", f"{types['post_type'].nunique():,}")
        st.metric("Records", f"{types['posts'].sum():,.0f}")
        type_reach_total = types["reach"].sum(min_count=1)
        type_engagement_total = types["engagements"].sum(min_count=1)
        st.metric("Summed post reach", compact_number(type_reach_total),
                  help=f"Full value: {type_reach_total:,.0f}" if pd.notna(type_reach_total) else "No value available")
        st.metric("Engagements", compact_number(type_engagement_total),
                  help=f"Full value: {type_engagement_total:,.0f}" if pd.notna(type_engagement_total) else "No value available")
    if not types.empty and types["weighted_engagement_rate"].notna().any():
        best = types.dropna(subset=["weighted_engagement_rate"]).iloc[0]
        takeaway(
            f"<b>{best['post_type']}</b> has the highest weighted engagement rate "
            f"({best['weighted_engagement_rate']:.2%}) across {best['posts']:,.0f} records "
            f"and {best['reach']:,.0f} summed post reach. "
            "Use this as a test candidate, not proof that the format itself caused stronger engagement."
        )
    else:
        takeaway("No post type has a calculable engagement rate in the current selection.")

with col2:
    camp = (
        comparison_data.groupby("campaign_type", dropna=False)
        .agg(
            posts=("campaign_type", "size"),
            engagements=("total_engagements", lambda s: s.sum(min_count=1)),
            reach=("reach", lambda s: s.sum(min_count=1)),
            follows=("follows", lambda s: s.sum(min_count=1)),
        )
        .reset_index()
    )
    camp["weighted_engagement_rate"] = camp["engagements"] / camp["reach"].where(camp["reach"] > 0)
    camp = camp.sort_values("weighted_engagement_rate", ascending=False, na_position="last")
    chart_area, metric_area = st.columns([2.25, 1], gap="small")
    with chart_area:
        camp_fig = px.bar(
            camp,
            x="campaign_type",
            y="weighted_engagement_rate",
            title="Weighted engagement rate by campaign",
            labels={"campaign_type": "Campaign", "weighted_engagement_rate": "Weighted engagement rate"},
            color="campaign_type", color_discrete_sequence=CHART_COLORS,
            text=camp["weighted_engagement_rate"].map(lambda value: f"{value:.1%}" if pd.notna(value) else "—"),
        )
        camp_fig.update_traces(
            textposition="outside", cliponaxis=False,
            marker_line_color="rgba(255,244,248,0.55)", marker_line_width=1,
            customdata=camp[["posts", "reach", "engagements"]].to_numpy(),
            hovertemplate=("<b>%{x}</b><br>Weighted engagement rate: %{y:.2%}"
                           "<br>Records: %{customdata[0]:,.0f}"
                           "<br>Summed post reach: %{customdata[1]:,.0f}"
                           "<br>Engagements: %{customdata[2]:,.0f}<extra></extra>"),
        )
        camp_fig.update_layout(**PLOT_LAYOUT, showlegend=False, height=490)
        camp_fig.update_yaxes(tickformat=".1%", rangemode="tozero")
        st.plotly_chart(camp_fig, width="stretch")
    with metric_area:
        st.markdown("**Campaign at a glance**")
        st.metric("Campaigns", f"{camp['campaign_type'].nunique():,}")
        st.metric("Records", f"{camp['posts'].sum():,.0f}")
        reach_total = camp["reach"].sum(min_count=1)
        engagement_total = camp["engagements"].sum(min_count=1)
        st.metric("Summed post reach", compact_number(reach_total),
                  help=f"Full value: {reach_total:,.0f}" if pd.notna(reach_total) else "No value available")
        st.metric("Engagements", compact_number(engagement_total),
                  help=f"Full value: {engagement_total:,.0f}" if pd.notna(engagement_total) else "No value available")
    if not camp.empty and camp["weighted_engagement_rate"].notna().any():
        best_campaign = camp.dropna(subset=["weighted_engagement_rate"]).iloc[0]
        takeaway(
            f"<b>{best_campaign['campaign_type']}</b> has the highest weighted engagement rate "
            f"({best_campaign['weighted_engagement_rate']:.2%}) across "
            f"{best_campaign['posts']:,.0f} records and {best_campaign['reach']:,.0f} summed post reach. "
            "Validate this pattern across comparable posts before prioritising effort."
        )
    else:
        takeaway("No campaign has a calculable engagement rate in the current selection.")

# Additional management context: engagement mix and audience-action trend.
st.subheader("Engagement drivers and audience actions")
engagement_columns = [c for c in ["likes", "comments", "shares", "saves"] if c in f.columns]
left_extra, right_extra = st.columns(2)
with left_extra:
    if engagement_columns:
        mix = pd.DataFrame({"Interaction": engagement_columns, "Total": [pd.to_numeric(f[c], errors="coerce").sum(min_count=1) for c in engagement_columns]})
        mix = mix.dropna(subset=["Total"])
        mix_fig = px.bar(mix, x="Interaction", y="Total", color="Interaction", text=mix["Total"].map(lambda x: f"{x:,.0f}"), title="Interaction mix across selected records", color_discrete_sequence=CHART_COLORS)
        mix_fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{x}<br>Interactions: %{y:,.0f}<extra></extra>")
        mix_fig.update_layout(**PLOT_LAYOUT, showlegend=False)
        st.plotly_chart(mix_fig, width="stretch")
        total_interactions = mix["Total"].sum()
        dominant = mix.loc[mix["Total"].idxmax()]
        takeaway(f"<b>{dominant['Interaction'].title()}</b> is the largest recorded interaction category ({dominant['Total']:,.0f}; {dominant['Total']/total_interactions:.1%} of the displayed interaction mix). Consider this a volume signal, not a measure of interaction quality.")
    else:
        st.info("Like/comment/share/save fields are not available for an interaction-mix chart.")
with right_extra:
    action_columns = [c for c in ["profile_visits", "follows"] if c in f.columns]
    if action_columns and f["post_date"].notna().any():
        action_data = f.dropna(subset=["post_date"]).copy()
        for c in action_columns:
            action_data[c] = pd.to_numeric(action_data[c], errors="coerce")
        action_monthly = action_data.assign(month=action_data["post_date"].dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False)[action_columns].sum(min_count=1)
        action_long = action_monthly.melt(id_vars="month", value_vars=action_columns, var_name="Metric", value_name="Count")
        action_long["Metric"] = action_long["Metric"].replace({"profile_visits": "Profile visits", "follows": "Follows"})
        action_fig = px.line(action_long, x="month", y="Count", color="Metric", markers=True, title="Monthly profile visits and follows", color_discrete_sequence=CHART_COLORS)
        action_fig.update_traces(line=dict(width=3), hovertemplate="%{x|%b %Y}<br>%{fullData.name}: %{y:,.0f}<extra></extra>")
        action_fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(action_fig, width="stretch")
        if "profile_visits" in action_columns and "follows" in action_columns:
            visits = pd.to_numeric(f["profile_visits"], errors="coerce").sum(min_count=1)
            follows_total = pd.to_numeric(f["follows"], errors="coerce").sum(min_count=1)
            proxy = follows_total / visits if pd.notna(visits) and visits > 0 and pd.notna(follows_total) else float("nan")
            takeaway(f"Aggregate follows ÷ profile visits proxy: <b>{proxy:.2%}</b>. This is not a user-level conversion rate; the dataset cannot link a particular visit to a particular follow." if pd.notna(proxy) else "The follow-per-profile-visit proxy cannot be calculated for the selected records.")
    else:
        st.info("Profile visit/follow trend is shown when those fields are present in the selected dataset.")

st.subheader("Management readout")
management_points = []
if not types.empty and types["weighted_engagement_rate"].notna().any():
    best_type = types.dropna(subset=["weighted_engagement_rate"]).iloc[0]
    management_points.append(f"**Content test:** run a controlled follow-up test for {best_type['post_type']} content, the highest observed format by weighted engagement rate ({best_type['weighted_engagement_rate']:.2%}).")
if not camp.empty and camp["weighted_engagement_rate"].notna().any():
    best_camp = camp.dropna(subset=["weighted_engagement_rate"]).iloc[0]
    management_points.append(f"**Campaign review:** examine what distinguishes {best_camp['campaign_type']} records before shifting resources; the comparison is observational, not causal.")
management_points.append("**Measurement priority:** confirm data provenance and whether each row represents a unique post before treating record counts as publishing volume.")
management_points.append("**Reporting guardrail:** summed post reach is not unique account reach; ROI cannot be inferred without spend and revenue attribution.")
with st.container(border=True):
    for point in management_points:
        st.markdown(f"- {point}")

st.caption(
    "Comparisons are descriptive. Differences do not establish that a format or campaign caused engagement. "
    "Reach is summed across records and should not be interpreted as unique account-level reach. "
    "Monthly rates use summed engagements ÷ summed reach and a zero-based axis; months with zero or unavailable reach have no rate."
)

st.divider()
st.caption("Sugar Cosmetics Instagram Performance Analytics · Streamlit · Results are based on the selected supplied dataset.")
