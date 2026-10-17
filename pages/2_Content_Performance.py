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

st.set_page_config(page_title="SUGAR | Instagram Intelligence", page_icon="💄", layout="wide", initial_sidebar_state="expanded")
context = initialize("Content Performance")
globals().update(context)

COLORS = ["#F05291", "#9B4D78", "#F6A6C1", "#C43D73", "#D77AA5", "#6E3157", "#F7C6D8", "#B65A88"]

def takeaway(message):
    st.markdown(
        f"""
        <div style="margin:.45rem 0 .2rem;padding:.8rem 1rem;border:1px solid rgba(240,82,145,.35);
        border-left:4px solid #F05291;border-radius:10px;background:rgba(240,82,145,.08);
        line-height:1.55;">
        <strong style="color:#F6A6C1;">KEY TAKEAWAY</strong><br>{html.escape(str(message))}
        </div>
        """,
        unsafe_allow_html=True,
    )

def card_title(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

def interactive_table(df, key, *, numeric_formats=None, default_sort=None, height=380):
    """Searchable, sortable table with configurable row count and CSV export."""
    numeric_formats = numeric_formats or {}
    view = df.copy()
    toolbar = st.columns([1.7, 1.1, 0.8, 0.8])
    with toolbar[0]:
        search = st.text_input("Search table", key=f"{key}_search", placeholder="Search any column…")
    with toolbar[1]:
        sort_options = list(view.columns)
        initial_sort = default_sort if default_sort in sort_options else (sort_options[0] if sort_options else None)
        sort_by = st.selectbox("Sort by", sort_options, index=sort_options.index(initial_sort) if initial_sort in sort_options else 0, key=f"{key}_sort") if sort_options else None
    with toolbar[2]:
        descending = st.checkbox("Descending", value=True, key=f"{key}_desc")
    with toolbar[3]:
        row_limit = st.selectbox("Rows", [10, 25, 50, 100], index=0, key=f"{key}_rows")

    if search.strip():
        needle = search.strip().casefold()
        mask = view.astype(str).apply(lambda col: col.str.casefold().str.contains(needle, regex=False, na=False)).any(axis=1)
        view = view.loc[mask]
    if sort_by and sort_by in view.columns:
        try:
            view = view.sort_values(sort_by, ascending=not descending, na_position="last", key=None)
        except (TypeError, ValueError):
            view = view.sort_values(sort_by, ascending=not descending, na_position="last")

    st.caption(f"Showing {min(len(view), row_limit):,} of {len(view):,} matching rows · Click column headers to sort further.")
    shown = view.head(row_limit).copy()
    column_config = {}
    for col, fmt in numeric_formats.items():
        if col in shown.columns:
            if fmt == "percent":
                column_config[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                # Convert proportions to percentage points for the display format.
                shown[col] = pd.to_numeric(shown[col], errors="coerce") * 100
            elif fmt == "integer":
                column_config[col] = st.column_config.NumberColumn(col, format="%,.0f")
            elif fmt == "decimal":
                column_config[col] = st.column_config.NumberColumn(col, format="%,.1f")
    st.dataframe(shown, use_container_width=True, hide_index=True, height=height, column_config=column_config)
    st.download_button(
        "Download filtered table as CSV", data=view.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv", mime="text/csv", key=f"{key}_download",
    )

st.caption("Review content volume, reach, and engagement outcomes using the filters below.")

# Keep one stable sidebar slot so the page summary is redrawn with each filter change.
sidebar_summary = st.sidebar.empty()

with st.container(border=True):
    # Content performance KPIs
    st.markdown("## Content performance")
    content_source = f.copy()
    kpi_placeholder = st.empty()

    # Content-specific filters sit directly below the KPI row.
    with st.container(border=True):
        card_title(
            "Content performance filters",
            "Combine filters to narrow the records used by every KPI, chart, table, and the sidebar summary.",
        )

        dates = pd.to_datetime(content_source["post_date"], errors="coerce").dropna()
        if not dates.empty:
            date_min = dates.min().date()
            date_max = dates.max().date()
        else:
            date_min = date_max = None

        post_types = sorted(content_source["post_type"].dropna().astype(str).unique().tolist())
        campaigns = sorted(content_source["campaign_type"].dropna().astype(str).unique().tolist())
        hashtag_values = (
            sorted(content_source["hashtags"].dropna().astype(str).unique().tolist())
            if "hashtags" in content_source.columns else []
        )

        row1 = st.columns([1.2, 1, 1.2, 1])
        if date_min is not None:
            with row1[0]:
                selected_dates = st.date_input(
                    "Post date range", value=(date_min, date_max),
                    min_value=date_min, max_value=date_max,
                    key="content_perf_date_range",
                )
        else:
            selected_dates = ()

        with row1[1]:
            selected_types = st.multiselect(
                "Content format", options=post_types, default=post_types,
                key="content_perf_post_types",
            )
        with row1[2]:
            selected_campaigns = st.multiselect(
                "Campaign type", options=campaigns, default=campaigns,
                key="content_perf_campaign_types",
            )
        with row1[3]:
            min_reach = st.number_input(
                "Minimum reach", min_value=0, value=0, step=100,
                key="content_perf_min_reach",
            )

        row2 = st.columns([1.2, 1.4, 1.2, 1.2])
        with row2[0]:
            min_engagements = st.number_input(
                "Minimum engagements", min_value=0, value=0, step=100,
                key="content_perf_min_engagements",
            )
        with row2[1]:
            if hashtag_values:
                selected_hashtags = st.multiselect(
                    "Hashtag / hashtag text", options=hashtag_values,
                    default=hashtag_values, key="content_perf_hashtags",
                    help="Matches records whose hashtag field contains at least one selected value.",
                )
            else:
                selected_hashtags = []
                st.caption("Hashtag filter unavailable: no hashtag column found.")
        with row2[2]:
            interaction_metric = st.selectbox(
                "Interaction metric", ["Likes", "Comments", "Shares", "Saves"],
                index=0, key="content_perf_interaction_metric",
                help="Choose which interaction count the minimum threshold should use.",
            )
        with row2[3]:
            min_interactions = st.number_input(
                "Minimum selected interaction", min_value=0, value=0, step=10,
                key="content_perf_min_interactions",
                help="Records must meet or exceed this count for the selected interaction metric.",
            )

        rate_values = pd.to_numeric(content_source["engagement_rate"], errors="coerce").dropna() if "engagement_rate" in content_source.columns else pd.Series(dtype=float)
        if not rate_values.empty:
            rate_min = max(0.0, float(rate_values.min()))
            rate_max = min(1.0, float(rate_values.max()))
            if rate_max < rate_min:
                rate_max = rate_min
            with st.container():
                selected_rate_range = st.slider(
                    "Engagement rate range",
                    min_value=rate_min, max_value=rate_max,
                    value=(rate_min, rate_max), step=0.001,
                    format="%.3f", key="content_perf_rate_range",
                    help="Values use the dataset's engagement_rate scale (usually 0–1, displayed as a proportion).",
                )
        else:
            selected_rate_range = None

        st.caption("Use the filters together. The selected interaction threshold is applied in addition to reach and engagement-rate limits.")

    # Apply all filters to one shared dataframe so every downstream visual stays consistent.
    f = content_source.copy()
    if selected_dates and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        post_dates = pd.to_datetime(f["post_date"], errors="coerce").dt.date
        f = f[(post_dates >= start_date) & (post_dates <= end_date)]
    f = f[f["post_type"].fillna("").astype(str).isin(selected_types)]
    f = f[f["campaign_type"].fillna("").astype(str).isin(selected_campaigns)]
    f = f[pd.to_numeric(f["reach"], errors="coerce").fillna(0) >= min_reach]
    f = f[pd.to_numeric(f["total_engagements"], errors="coerce").fillna(0) >= min_engagements]

    if selected_rate_range is not None:
        rates = pd.to_numeric(f["engagement_rate"], errors="coerce")
        f = f[rates.between(selected_rate_range[0], selected_rate_range[1], inclusive="both")]

    if hashtag_values and selected_hashtags:
        hashtag_text = f["hashtags"].fillna("").astype(str).str.lower()
        selected_lower = [tag.lower() for tag in selected_hashtags]
        hashtag_mask = hashtag_text.apply(lambda value: any(tag in value for tag in selected_lower))
        f = f[hashtag_mask]
    elif hashtag_values and not selected_hashtags:
        f = f.iloc[0:0]

    interaction_columns = {
        "Likes": "likes", "Comments": "comments", "Shares": "shares", "Saves": "saves"
    }
    interaction_column = interaction_columns[interaction_metric]
    f = f[pd.to_numeric(f[interaction_column], errors="coerce").fillna(0) >= min_interactions]

    total_posts = len(f)
    total_engagements = pd.to_numeric(f["total_engagements"], errors="coerce").fillna(0).sum()
    total_reach = pd.to_numeric(f["reach"], errors="coerce").fillna(0).sum()
    avg_engagement_rate = pd.to_numeric(f["engagement_rate"], errors="coerce").mean()
    avg_engagements = pd.to_numeric(f["total_engagements"], errors="coerce").mean()

    # Dynamic page-specific summary appears below the native sidebar navigation.
    if not f.empty:
        sidebar_formats = f.assign(
            _engagements=pd.to_numeric(f["total_engagements"], errors="coerce")
        ).groupby("post_type", dropna=False)["_engagements"].mean()
        top_format = str(sidebar_formats.idxmax()) if not sidebar_formats.empty else "—"
        if top_format == "nan":
            top_format = "Unknown"
        sidebar_dates = pd.to_datetime(f["post_date"], errors="coerce").dropna()
        sidebar_period = (
            f"{sidebar_dates.min():%d %b %Y} – {sidebar_dates.max():%d %b %Y}"
            if not sidebar_dates.empty else "Date range unavailable"
        )
    else:
        top_format = "—"
        sidebar_period = "No matching records"

    sidebar_rate = f"{avg_engagement_rate:.2%}" if pd.notna(avg_engagement_rate) else "—"
    sidebar_engagements = f"{total_engagements:,.0f}"
    sidebar_reach = f"{total_reach:,.0f}"
    with sidebar_summary.container():
        st.markdown(
            f"""
            <div class="sugar-sidebar-info">
                <div class="sugar-sidebar-eyebrow">SUGAR COSMETICS · CURRENT PAGE</div>
            <div class="sugar-sidebar-title">Content Performance</div>
            <div class="sugar-sidebar-description">
                A live summary of the content currently included by your filters.
            </div>
            <div class="sugar-sidebar-divider"></div>
            <div class="sugar-sidebar-stat"><span>Analysis period</span><strong>{html.escape(sidebar_period)}</strong></div>
            <div class="sugar-sidebar-stat"><span>Records analysed</span><strong>{total_posts:,}</strong></div>
            <div class="sugar-sidebar-stat"><span>Total engagements</span><strong>{sidebar_engagements}</strong></div>
            <div class="sugar-sidebar-stat"><span>Total post reach</span><strong>{sidebar_reach}</strong></div>
            <div class="sugar-sidebar-stat"><span>Average engagement rate</span><strong>{sidebar_rate}</strong></div>
            <div class="sugar-sidebar-stat"><span>Top format by avg. engagements</span><strong>{html.escape(top_format)}</strong></div>
            <div class="sugar-sidebar-foot">Updates automatically when the content filters change.</div>
        </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_placeholder.container():
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Content records", f"{total_posts:,}")
        k2.metric("Total engagements", f"{total_engagements:,.0f}")
        k3.metric("Total post reach", f"{total_reach:,.0f}")
        k4.metric("Average engagement rate", f"{avg_engagement_rate:.2%}" if pd.notna(avg_engagement_rate) else "—")
        k5.metric("Avg. engagements / post", f"{avg_engagements:,.1f}" if pd.notna(avg_engagements) else "—")

    if f.empty:
        st.warning("No content records match these filters. Broaden the date range or relax one or more thresholds.")
    else:
        comp = f.groupby("post_type", dropna=False).agg(
            records=("post_type", "size"),
            avg_likes=("likes", "mean"),
            avg_comments=("comments", "mean"),
            avg_shares=("shares", "mean"),
            avg_saves=("saves", "mean"),
            reach=("reach", "sum"),
            engagements=("total_engagements", "sum"),
        ).reset_index()
        comp["weighted_engagement_rate"] = comp["engagements"].div(comp["reach"].replace(0, pd.NA))
        comp["post_type"] = comp["post_type"].fillna("Unknown").astype(str)

        with st.container(border=True):
            card_title("Average interactions by content format", "Compare likes, comments, shares and saves per record.")
            melt = comp.melt(
                id_vars="post_type",
                value_vars=["avg_likes", "avg_comments", "avg_shares", "avg_saves"],
                var_name="metric",
                value_name="average",
            )
            melt["metric"] = melt["metric"].map({
                "avg_likes": "Likes", "avg_comments": "Comments",
                "avg_shares": "Shares", "avg_saves": "Saves",
            })
            fig = px.bar(
                melt, x="post_type", y="average", color="metric", barmode="group",
                color_discrete_sequence=COLORS,
                labels={"post_type": "Content format", "average": "Average interactions", "metric": "Interaction"},
            )
            fig.update_layout(template="sugar", legend_title_text="", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
            if not melt.empty and melt["average"].notna().any():
                interaction_means = melt.groupby("metric")["average"].mean().dropna()
                top_interaction = interaction_means.idxmax() if not interaction_means.empty else "Interactions"
                best = comp.sort_values("weighted_engagement_rate", ascending=False).iloc[0]
                rate = best["weighted_engagement_rate"]
                rate_text = f"{rate:.2%}" if pd.notna(rate) else "unavailable"
                takeaway(f"{top_interaction} has the highest average per-record volume across the formats. {best['post_type']} has the highest weighted engagement rate ({rate_text}); observed association does not prove that the format caused the result.")

        with st.container(border=True):
            card_title("Engagement rate by content format", "Weighted engagement rate = summed engagements ÷ summed post reach.")
            rate_comp = comp.sort_values("weighted_engagement_rate", ascending=True)
            fig = px.bar(
                rate_comp, x="weighted_engagement_rate", y="post_type", orientation="h",
                text=rate_comp["weighted_engagement_rate"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "—"),
                color="weighted_engagement_rate",
                color_continuous_scale=["#FADCE8", "#F05291", "#6E3157"],
                labels={"post_type": "Content format", "weighted_engagement_rate": "Weighted engagement rate"},
            )
            fig.update_layout(template="sugar", coloraxis_showscale=False, xaxis_tickformat=".0%", margin=dict(l=10, r=35, t=15, b=10))
            st.plotly_chart(fig, use_container_width=True)
            if not rate_comp.empty:
                best = rate_comp.sort_values("weighted_engagement_rate", ascending=False).iloc[0]
                rate = best["weighted_engagement_rate"]
                takeaway(f"{best['post_type']} leads on weighted engagement rate ({rate:.2%}) based on {int(best['records']):,} records." if pd.notna(rate) else "A weighted engagement rate could not be calculated because reach is missing or zero.")

        with st.container(border=True):
            card_title("Top 10 content records by likes", "Identify records with the largest like counts.")
            top_likes = f.nlargest(10, "likes")[["post_date", "post_type", "campaign_type", "likes", "comments", "shares", "saves", "reach", "hashtags"]].copy()
            interactive_table(
                top_likes, "top_content_by_likes",
                numeric_formats={"likes": "integer", "comments": "integer", "shares": "integer", "saves": "integer", "reach": "integer"},
                default_sort="likes", height=390,
            )
            if not top_likes.empty:
                r = top_likes.iloc[0]
                takeaway(f"The most-liked record is dated {pd.Timestamp(r['post_date']):%d %b %Y} ({r['post_type']}, {r['campaign_type']}) with {r['likes']:,.0f} likes.")

        with st.container(border=True):
            card_title("Top 10 content records by engagement rate", "High rates should be reviewed alongside reach and interaction volume.")
            top_rate = f.nlargest(10, "engagement_rate")[["post_date", "post_type", "campaign_type", "engagement_rate", "total_engagements", "reach", "hashtags"]].copy()
            interactive_table(
                top_rate, "top_content_by_engagement_rate",
                numeric_formats={"engagement_rate": "percent", "total_engagements": "integer", "reach": "integer"},
                default_sort="engagement_rate", height=390,
            )
            if not top_rate.empty:
                r = top_rate.iloc[0]
                takeaway(f"The highest-rate record is dated {pd.Timestamp(r['post_date']):%d %b %Y} at {r['engagement_rate']:.2%}. Check its reach denominator before treating it as a repeatable benchmark.")

        with st.container(border=True):
            card_title("Content format performance table", "Use this table to compare post volume, interaction averages, reach and weighted engagement rate.")
            display_comp = comp.rename(columns={
                "post_type": "Content format", "records": "Records", "avg_likes": "Avg. likes",
                "avg_comments": "Avg. comments", "avg_shares": "Avg. shares", "avg_saves": "Avg. saves",
                "reach": "Summed reach", "engagements": "Total engagements",
                "weighted_engagement_rate": "Weighted engagement rate",
            })
            interactive_table(
                display_comp, "content_format_performance",
                numeric_formats={
                    "Records": "integer", "Avg. likes": "decimal", "Avg. comments": "decimal",
                    "Avg. shares": "decimal", "Avg. saves": "decimal", "Summed reach": "integer",
                    "Total engagements": "integer", "Weighted engagement rate": "percent",
                },
                default_sort="Weighted engagement rate", height=300,
            )
            best_by_rate = comp.sort_values("weighted_engagement_rate", ascending=False).iloc[0]
            takeaway(f"Use the format-level table to balance engagement rate with record count and total reach; the highest rate alone may not represent the largest overall contribution.")

