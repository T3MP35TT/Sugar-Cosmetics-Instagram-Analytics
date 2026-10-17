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

st.set_page_config(
    page_title="SUGAR | Instagram Intelligence",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

context = initialize("Audience & Conversion")
globals().update(context)


def takeaway(message):
    st.markdown(
        f"""
        <div style="margin:.3rem 0 1rem;padding:.85rem 1rem;
        border-left:4px solid #F05291;border-radius:0 9px 9px 0;
        background:rgba(240,82,145,.10);color:#F8EAF1;line-height:1.55;">
        <span style="font-weight:800;color:#F6A6C1;">KEY TAKEAWAY</span><br>
        {html.escape(str(message))}
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_sum(frame, column):
    """Sum a numeric metric safely, treating invalid/missing values as zero."""
    if column not in frame.columns:
        return 0
    return pd.to_numeric(frame[column], errors="coerce").fillna(0).sum()


def safe_rate(numerator, denominator):
    """Return a ratio, or None when the denominator is zero/invalid."""
    try:
        numerator = float(numerator)
        denominator = float(denominator)
    except (TypeError, ValueError):
        return None
    if pd.isna(numerator) or pd.isna(denominator) or denominator <= 0:
        return None
    return numerator / denominator


def rate_label(value):
    return "—" if value is None or pd.isna(value) else f"{value:.2%}"


def prepare_rate(numerator, denominator):
    """Vectorized safe division that leaves undefined rates as NaN."""
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return numerator.div(denominator.where(denominator > 0))


page_kpis("Audience & Conversion", f)
st.caption(
    "Explore aggregate reach, profile visits, follows, engagement sources, "
    "recorded emotion labels and post-format action rates."
)

with st.container(border=True):
    st.markdown("### Audience and conversion filters")
    c1, c2, c3, c4 = st.columns(4)

    dates_series = pd.to_datetime(f["post_date"], errors="coerce").dropna()
    if dates_series.empty:
        st.error("The dataset does not contain usable post dates.")
        st.stop()

    dmin = dates_series.min().date()
    dmax = dates_series.max().date()
    dates = c1.date_input(
        "Post date range",
        value=(dmin, dmax),
        min_value=dmin,
        max_value=dmax,
        key="audience_combined_dates",
    )

    types = sorted(f["post_type"].dropna().astype(str).unique())
    chosen_types = c2.multiselect(
        "Post format", types, default=types, key="audience_combined_types"
    )
    campaigns = sorted(f["campaign_type"].dropna().astype(str).unique())
    chosen_campaigns = c3.multiselect(
        "Campaign type", campaigns, default=campaigns, key="audience_combined_campaigns"
    )
    sources = sorted(f["engagement_source"].dropna().astype(str).unique())
    chosen_sources = c4.multiselect(
        "Engagement source", sources, default=sources, key="audience_combined_sources"
    )
    emotions = sorted(f["audience_emotion"].dropna().astype(str).unique())
    chosen_emotions = st.multiselect(
        "Recorded audience emotion",
        emotions,
        default=emotions,
        key="audience_combined_emotions",
    )

page_data = f.copy()
page_data["post_date"] = pd.to_datetime(page_data["post_date"], errors="coerce")
if isinstance(dates, (tuple, list)) and len(dates) == 2:
    page_data = page_data[
        page_data["post_date"].dt.date.between(dates[0], dates[1], inclusive="both")
    ]
page_data = page_data[page_data["post_type"].astype(str).isin(chosen_types)]
page_data = page_data[page_data["campaign_type"].astype(str).isin(chosen_campaigns)]
page_data = page_data[page_data["engagement_source"].astype(str).isin(chosen_sources)]
page_data = page_data[page_data["audience_emotion"].astype(str).isin(chosen_emotions)]

if page_data.empty:
    st.warning("No records match these filters. Widen the date range or select more values.")
    st.stop()

f = page_data
page_kpis("Filtered audience outcomes", f)

reach = safe_sum(f, "reach")
visits = safe_sum(f, "profile_visits")
follows = safe_sum(f, "follows")
visit_rate = safe_rate(visits, reach)
follow_visit_rate = safe_rate(follows, visits)
follow_reach_rate = safe_rate(follows, reach)

st.markdown("## Audience journey")
st.caption(
    f"Analysing {len(f):,} records from "
    f"{f['post_date'].min():%d %b %Y} to {f['post_date'].max():%d %b %Y}."
)

# Separate absolute audience volumes from step-to-step conversion proxies.
# These aggregate totals are not verified person-level funnel counts.
journey = pd.DataFrame(
    {
        "Stage": ["Reach", "Profile visits", "Follows"],
        "Total volume": [reach, visits, follows],
    }
)
journey["Share of reach"] = journey["Total volume"].map(
    lambda value: (value / reach * 100) if reach > 0 else float("nan")
)

st.markdown("### Audience volume")
st.caption("Summed totals for the selected records; reach is not unique account-level reach.")
v1, v2, v3 = st.columns(3)
v1.metric("Reach", f"{reach:,.0f}")
v2.metric("Profile visits", f"{visits:,.0f}")
v3.metric("Follows", f"{follows:,.0f}")

st.markdown("### Conversion journey")
step_rates = pd.DataFrame(
    {
        "Step": ["Reach → profile visits", "Profile visits → follows"],
        "Conversion rate": [visit_rate, follow_visit_rate],
        "Numerator": [visits, follows],
        "Denominator": [reach, visits],
    }
)
step_rates["Rate label"] = step_rates["Conversion rate"].map(rate_label)
step_rates["Numerator label"] = step_rates["Numerator"].map(lambda value: f"{value:,.0f}")
step_rates["Denominator label"] = step_rates["Denominator"].map(lambda value: f"{value:,.0f}")
valid_steps = step_rates.dropna(subset=["Conversion rate"]).copy()
if not valid_steps.empty:
    fig = px.bar(
        valid_steps,
        x="Conversion rate",
        y="Step",
        orientation="h",
        text="Rate label",
        color="Step",
        color_discrete_map={
            "Reach → profile visits": "#F05291",
            "Profile visits → follows": "#6E3157",
        },
        custom_data=["Numerator label", "Denominator label"],
        title="Step conversion rates · each step uses its previous stage as denominator",
        category_orders={"Step": ["Profile visits → follows", "Reach → profile visits"]},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "%{y}<br>Conversion rate: %{x:.2%}"
            "<br>Next-stage total: %{customdata[0]}"
            "<br>Previous-stage total: %{customdata[1]}<extra></extra>"
        ),
    )
    max_rate = max(float(valid_steps["Conversion rate"].max()), 0.01)
    fig.update_layout(
        template="sugar",
        showlegend=False,
        xaxis_title="Conversion rate",
        yaxis_title="",
        xaxis=dict(range=[0, max_rate * 1.3], tickformat=".0%", rangemode="tozero"),
        margin=dict(l=20, r=55, t=60, b=25),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Conversion rates are undefined because the selected denominators are zero.")

with st.expander("View absolute audience journey totals"):
    display_journey = journey[["Stage", "Total volume", "Share of reach"]].copy()
    display_journey["Total volume"] = display_journey["Total volume"].map(lambda value: f"{value:,.0f}")
    display_journey["Share of reach"] = display_journey["Share of reach"].map(
        lambda value: f"{value:.2f}%" if pd.notna(value) else "—"
    )
    st.dataframe(display_journey, use_container_width=True, hide_index=True)

takeaway(
    f"{rate_label(visit_rate)} of summed reach is associated with profile visits, "
    f"and {rate_label(follow_visit_rate)} of profile visits is associated with follows. "
    "These are aggregate proxy ratios, not verified person-by-person conversions."
)
a, b, c = st.columns(3)
a.metric("Profile visits / reach", rate_label(visit_rate))
b.metric("Follows / profile visits", rate_label(follow_visit_rate))
c.metric("Follows / reach", rate_label(follow_reach_rate))

st.divider()
st.markdown("## Engagement funnel detail")
st.caption(
    "These are aggregate exposure and interaction totals, not sequential funnel stages. "
    "Reach and impressions can overlap across posts."
)

totals2 = pd.DataFrame(
    {
        "Metric": ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"],
        "Volume": [
            safe_sum(f, "impressions"),
            reach,
            safe_sum(f, "likes"),
            safe_sum(f, "comments"),
            safe_sum(f, "shares"),
            safe_sum(f, "saves"),
        ],
    }
)
totals2["Volume"] = pd.to_numeric(totals2["Volume"], errors="coerce").fillna(0)
totals2["Volume label"] = totals2["Volume"].map(lambda value: f"{value:,.0f}")

# Exposure and engagement actions have very different magnitudes. Plot them
# separately so the large impressions/reach totals do not flatten the action bars.
exposure = totals2[totals2["Metric"].isin(["Impressions", "Reach"])].copy()
actions = totals2[totals2["Metric"].isin(["Likes", "Comments", "Shares", "Saves"])].copy()

st.markdown("### Exposure volume")
st.caption("Impressions and reach use their own scale, separate from engagement actions.")
fig_exposure = px.bar(
    exposure,
    x="Metric",
    y="Volume",
    color="Metric",
    text="Volume label",
    color_discrete_map={"Impressions": "#F05291", "Reach": "#9B4D78"},
    title="Aggregate exposure volume",
)
fig_exposure.update_traces(textposition="outside", cliponaxis=False)
fig_exposure.update_layout(
    template="sugar",
    showlegend=False,
    yaxis_title="Total volume",
    yaxis_tickformat=",",
    yaxis_rangemode="tozero",
    margin=dict(l=15, r=25, t=65, b=15),
)
st.plotly_chart(fig_exposure, use_container_width=True)

st.markdown("### Engagement action volume")
st.caption("Likes, comments, shares and saves use a separate scale so smaller actions remain visible.")
fig_actions = px.bar(
    actions,
    x="Metric",
    y="Volume",
    color="Metric",
    text="Volume label",
    color_discrete_map={
        "Likes": "#F6A6C1",
        "Comments": "#C43D73",
        "Shares": "#D77AA5",
        "Saves": "#6E3157",
    },
    title="Aggregate engagement actions",
)
fig_actions.update_traces(textposition="outside", cliponaxis=False)
fig_actions.update_layout(
    template="sugar",
    showlegend=False,
    yaxis_title="Total actions",
    yaxis_tickformat=",",
    yaxis_rangemode="tozero",
    margin=dict(l=15, r=25, t=65, b=15),
)
st.plotly_chart(fig_actions, use_container_width=True)

takeaway(
    "Impressions and reach measure exposure; likes, comments, shares and saves measure "
    "actions. This compares aggregate volumes, not sequential user-level funnel drop-off."
)

# Explicit string formatting prevents large integer totals from appearing blank
# in some dataframe/table render or print-to-PDF paths.
display_totals = totals2[["Metric", "Volume"]].copy()
display_totals["Volume"] = display_totals["Volume"].map(lambda value: f"{value:,.0f}")
st.dataframe(display_totals, use_container_width=True, hide_index=True)

st.divider()
st.markdown("## Which engagement sources are associated with outcomes?")
src = (
    f.groupby("engagement_source", dropna=False)
    .agg(
        records=("engagement_source", "size"),
        engagements=("total_engagements", "sum"),
        reach=("reach", "sum"),
        visits=("profile_visits", "sum"),
        follows=("follows", "sum"),
    )
    .reset_index()
)
for column in ["engagements", "reach", "visits", "follows"]:
    src[column] = pd.to_numeric(src[column], errors="coerce").fillna(0)

src["weighted_engagement_rate"] = prepare_rate(src["engagements"], src["reach"])
src["visit_rate"] = prepare_rate(src["visits"], src["reach"])
src["follow_visit_rate"] = prepare_rate(src["follows"], src["visits"])
src["engagement_source"] = src["engagement_source"].fillna("Not recorded").astype(str)
src = src.sort_values("weighted_engagement_rate", ascending=False, na_position="last")

valid_src = src.dropna(subset=["weighted_engagement_rate"])
if not valid_src.empty:
    fig = px.bar(
        valid_src,
        x="engagement_source",
        y="weighted_engagement_rate",
        color="weighted_engagement_rate",
        text=valid_src["weighted_engagement_rate"].map(lambda value: f"{value:.1%}"),
        color_continuous_scale=["#FADCE8", "#F05291", "#6E3157"],
        title="Weighted engagement rate by source",
        labels={
            "engagement_source": "Engagement source",
            "weighted_engagement_rate": "Weighted engagement rate",
        },
        hover_data={"records": True, "reach": ":,.0f", "engagements": ":,.0f"},
    )
    fig.update_layout(
        template="sugar",
        coloraxis_showscale=False,
        yaxis_tickformat=".1%",
        margin=dict(l=15, r=15, t=60, b=15),
    )
    st.plotly_chart(fig, use_container_width=True)
    best = valid_src.iloc[0]
    takeaway(
        f"{best['engagement_source']} has the highest weighted engagement rate "
        f"({best['weighted_engagement_rate']:.2%}) among selected sources. "
        "Review record counts and reach before treating the ranking as conclusive."
    )
else:
    st.info("Weighted engagement rate is undefined for the selected sources because reach is zero.")

rates = src.melt(
    id_vars=["engagement_source", "records"],
    value_vars=["visit_rate", "follow_visit_rate"],
    var_name="measure",
    value_name="rate",
).dropna(subset=["rate"])
rates["measure"] = rates["measure"].map(
    {
        "visit_rate": "Profile visits / reach",
        "follow_visit_rate": "Follows / profile visits",
    }
)
if not rates.empty:
    fig = px.bar(
        rates,
        x="engagement_source",
        y="rate",
        color="measure",
        barmode="group",
        color_discrete_map={
            "Profile visits / reach": "#F05291",
            "Follows / profile visits": "#6E3157",
        },
        title="Audience action-rate proxies by source",
        labels={
            "engagement_source": "Engagement source",
            "rate": "Rate",
            "measure": "Metric",
        },
        hover_data={"records": True},
    )
    fig.update_layout(
        template="sugar",
        yaxis_tickformat=".1%",
        margin=dict(l=15, r=15, t=60, b=15),
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)
    takeaway(
        "Compare both action rates alongside record counts. Differences are descriptive "
        "associations and may reflect campaign mix or sampling."
    )

st.divider()
st.markdown("## Recorded audience emotion and engagement")
emo = (
    f.groupby("audience_emotion", dropna=False)
    .agg(
        records=("audience_emotion", "size"),
        engagements=("total_engagements", "sum"),
        reach=("reach", "sum"),
    )
    .reset_index()
)
emo["engagements"] = pd.to_numeric(emo["engagements"], errors="coerce").fillna(0)
emo["reach"] = pd.to_numeric(emo["reach"], errors="coerce").fillna(0)
emo["weighted_engagement_rate"] = prepare_rate(emo["engagements"], emo["reach"])
emo["audience_emotion"] = emo["audience_emotion"].fillna("Not recorded").astype(str)
emo = emo.sort_values("weighted_engagement_rate", ascending=True, na_position="first")

valid_emo = emo.dropna(subset=["weighted_engagement_rate"])
if not valid_emo.empty:
    fig = px.bar(
        valid_emo,
        x="weighted_engagement_rate",
        y="audience_emotion",
        orientation="h",
        color="weighted_engagement_rate",
        text=valid_emo["weighted_engagement_rate"].map(lambda value: f"{value:.1%}"),
        color_continuous_scale=["#FADCE8", "#F05291", "#6E3157"],
        title="Weighted engagement rate by recorded emotion",
        labels={
            "audience_emotion": "Recorded label",
            "weighted_engagement_rate": "Weighted engagement rate",
        },
        hover_data={"records": True, "reach": ":,.0f", "engagements": ":,.0f"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        template="sugar",
        coloraxis_showscale=False,
        xaxis_tickformat=".1%",
        margin=dict(l=15, r=45, t=60, b=15),
    )
    st.plotly_chart(fig, use_container_width=True)
    best = valid_emo.iloc[-1]
    takeaway(
        f"{best['audience_emotion']} has the highest observed weighted engagement rate "
        f"({best['weighted_engagement_rate']:.2%}) among the selected recorded labels. "
        "This does not establish that emotion caused engagement."
    )
else:
    st.info("Engagement rates by recorded emotion are undefined because reach is zero.")

st.markdown("## Which post formats are linked to audience actions?")
fmt = (
    f.groupby("post_type", dropna=False)
    .agg(
        records=("post_type", "size"),
        reach=("reach", "sum"),
        visits=("profile_visits", "sum"),
        follows=("follows", "sum"),
    )
    .reset_index()
)
for column in ["reach", "visits", "follows"]:
    fmt[column] = pd.to_numeric(fmt[column], errors="coerce").fillna(0)
fmt["visit_rate"] = prepare_rate(fmt["visits"], fmt["reach"])
fmt["follow_visit_rate"] = prepare_rate(fmt["follows"], fmt["visits"])

long = fmt.melt(
    id_vars=["post_type", "records"],
    value_vars=["visit_rate", "follow_visit_rate"],
    var_name="measure",
    value_name="rate",
).dropna(subset=["rate"])
long["measure"] = long["measure"].map(
    {
        "visit_rate": "Profile visits / reach",
        "follow_visit_rate": "Follows / profile visits",
    }
)
if not long.empty:
    fig = px.bar(
        long,
        x="post_type",
        y="rate",
        color="measure",
        barmode="group",
        color_discrete_map={
            "Profile visits / reach": "#F05291",
            "Follows / profile visits": "#6E3157",
        },
        title="Audience action-rate proxies by post format",
        labels={"post_type": "Post format", "rate": "Rate", "measure": "Metric"},
        hover_data={"records": True},
    )
    fig.update_layout(
        template="sugar",
        yaxis_tickformat=".1%",
        margin=dict(l=15, r=15, t=60, b=15),
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)

    best = fmt.dropna(subset=["visit_rate"]).sort_values("visit_rate", ascending=False)
    if not best.empty:
        takeaway(
            f"{best.iloc[0]['post_type']} has the highest profile-visits-to-reach ratio "
            f"({best.iloc[0]['visit_rate']:.2%}) in the selected data. "
            "Compare record counts and campaign context too."
        )
else:
    st.info("Post-format action rates are undefined because the selected denominators are zero.")

st.caption(
    "The workbook does not include demographic fields or verified user-level journeys. "
    "Ratios are aggregate proxies, summed reach is not unique reach, and correlation "
    "does not demonstrate causation."
)
st.divider()
st.caption(
    "Sugar Cosmetics Instagram Performance Analytics · Results are based on the selected supplied dataset."
)
