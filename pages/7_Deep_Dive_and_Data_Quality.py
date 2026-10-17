from pathlib import Path
import sys

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

PALETTE = ["#FF5C8A", "#B388EB", "#58C4DD", "#FFB86B", "#7BD389", "#8EA7E9", "#F28482"]
PLOT_LAYOUT = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(18,18,27,0.55)", font=dict(family="Arial", color="#F7EAF1", size=12), margin=dict(l=12, r=12, t=42, b=12), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize

# Do not cache initialize(): it returns a dictionary containing modules and
# Streamlit helper functions, which cannot be pickled by st.cache_data.
# utils.common caches the expensive data-loading/validation/feature pipeline.
context = initialize("Deep Dive & Data Quality")
globals().update(context)

# The shared initializer already provides the prepared dataframe. Avoid copying
# and recalculating all derived columns on every rerun.
data = f

@st.cache_data(show_spinner=False, max_entries=8)
def dataframe_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")

# Compact, consistent formatting for rate KPIs.
def pct(value):
    return "—" if pd.isna(value) else f"{value:.2%}"

def number(value):
    return "—" if pd.isna(value) else f"{value:,.0f}"

def safe_sum(frame, column):
    if column not in frame.columns:
        return np.nan
    return pd.to_numeric(frame[column], errors="coerce").sum(min_count=1)

def weighted_rate(frame, numerator, denominator):
    if numerator not in frame.columns or denominator not in frame.columns:
        return np.nan
    num = pd.to_numeric(frame[numerator], errors="coerce")
    den = pd.to_numeric(frame[denominator], errors="coerce")
    valid = num.notna() & den.notna() & den.gt(0)
    if not valid.any():
        return np.nan
    return num.loc[valid].sum() / den.loc[valid].sum()

def add_filters(frame, key_prefix):
    """Reusable sidebar-style filters shown in the page body."""
    # Boolean filters below create the needed subsets; do not eagerly duplicate
    # all 50k rows before the user has changed any filters.
    filtered = frame
    with st.expander("Filter the analysis", expanded=True):
        top = st.columns(3)
        if "post_type" in filtered.columns:
            options = sorted(filtered["post_type"].dropna().astype(str).unique().tolist())
            selected = top[0].multiselect("Post type", options, default=options, key=f"{key_prefix}_post_type")
            if selected:
                filtered = filtered[filtered["post_type"].astype(str).isin(selected)]
            elif options:
                filtered = filtered.iloc[0:0]
        if "campaign_type" in filtered.columns:
            options = sorted(filtered["campaign_type"].dropna().astype(str).unique().tolist())
            selected = top[1].multiselect("Campaign type", options, default=options, key=f"{key_prefix}_campaign")
            if selected:
                filtered = filtered[filtered["campaign_type"].astype(str).isin(selected)]
            elif options:
                filtered = filtered.iloc[0:0]
        if "audience_emotion" in filtered.columns:
            options = sorted(filtered["audience_emotion"].dropna().astype(str).unique().tolist())
            selected = top[2].multiselect("Audience emotion", options, default=options, key=f"{key_prefix}_emotion")
            if selected:
                filtered = filtered[filtered["audience_emotion"].astype(str).isin(selected)]
            elif options:
                filtered = filtered.iloc[0:0]
        if "post_date" in filtered.columns and filtered["post_date"].notna().any():
            valid_dates = filtered["post_date"].dropna()
            min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
            chosen = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key=f"{key_prefix}_dates",
            )
            if isinstance(chosen, (tuple, list)) and len(chosen) == 2:
                start = pd.Timestamp(chosen[0])
                end_exclusive = pd.Timestamp(chosen[1]) + pd.Timedelta(1, unit="d")
                in_range = filtered["post_date"].ge(start) & filtered["post_date"].lt(end_exclusive)
                filtered = filtered[in_range | filtered["post_date"].isna()]
    return filtered

active_section = st.segmented_control(
    "Choose a section",
    options=["🔎 Deep Dive Explorer", "📊 Interactive Insights", "🛡️ Data Quality & Methodology"],
    default="🔎 Deep Dive Explorer",
    key="deep_dive_active_section",
    label_visibility="collapsed",
)

if active_section == "🔎 Deep Dive Explorer":
        st.subheader("Explore records")
        st.caption("Filter the dataset, find high-performing records, inspect individual rows, and export the filtered result.")
        view = add_filters(data, "explorer")

        search_cols = [c for c in ["hashtags", "post_type", "campaign_type", "audience_emotion", "engagement_source"] if c in view.columns]
        search = st.text_input(
            "Search records",
            placeholder="Try a hashtag, campaign, post type, or audience emotion",
            key="deep_dive_search",
        )
        if search.strip() and search_cols:
            mask = pd.Series(False, index=view.index)
            for col in search_cols:
                mask |= view[col].astype("string").str.contains(search.strip(), case=False, na=False, regex=False)
            view = view[mask]

        filtered_records = view
        available_sort_options = [
            "post_date", "engagement_rate", "total_engagements", "reach", "impressions",
            "likes", "comments", "shares", "saves", "profile_visits", "follows",
        ]
        sort_options = [c for c in available_sort_options if c in view.columns]
        controls = st.columns([2, 1, 1])
        if sort_options:
            default_sort = "engagement_rate" if "engagement_rate" in sort_options else sort_options[0]
            sort_by = controls[0].selectbox("Rank records by", sort_options, index=sort_options.index(default_sort), key="deep_dive_sort_column")
            descending = controls[1].selectbox("Order", ["Highest first", "Lowest first"], key="deep_dive_sort_direction") == "Highest first"
            show_rows = controls[2].selectbox("Rows shown", [25, 50, 100, 250, 500, 1000, "All"], index=2, key="deep_dive_row_limit")
        else:
            sort_by = None
            descending = True
            show_rows = "All"
            st.info("No supported fields are available for sorting.")

        k1, k2, k3 = st.columns(3)
        k1.metric("Matching records", f"{len(filtered_records):,}")
        k2.metric("Weighted engagement rate", pct(weighted_rate(filtered_records, "total_engagements", "reach")))
        k3.metric("Total engagements", number(safe_sum(filtered_records, "total_engagements")))
        st.caption("The row limit affects the table only; the CSV export contains every record matching the filters and search.")
        # Sorting is needed only for the visible table and explicit exports.
        # Avoid sorting all 50k rows on every widget rerun.
        if sort_by and not view.empty:
            if show_rows != "All" and sort_by in view.select_dtypes(include="number").columns:
                limit = int(show_rows)
                try:
                    view = view.nlargest(limit, sort_by) if descending else view.nsmallest(limit, sort_by)
                except (TypeError, ValueError):
                    view = filtered_records.sort_values(sort_by, ascending=not descending, na_position="last", kind="stable").head(limit)
                # Keep a deterministic ordering for the visible top/bottom N.
                view = view.sort_values(sort_by, ascending=not descending, na_position="last", kind="stable")
                display_view = view
            else:
                view = view.sort_values(sort_by, ascending=not descending, na_position="last", kind="stable")
                display_view = view if show_rows == "All" else view.head(int(show_rows))
        else:
            display_view = view if show_rows == "All" else view.head(int(show_rows))
        st.dataframe(display_view, width="stretch", hide_index=True, height=460)

        left, right = st.columns([1, 2])
        if "deep_dive_export_bytes" not in st.session_state:
            st.session_state["deep_dive_export_bytes"] = None
        if left.button("Prepare filtered CSV", key="prepare_deep_dive_csv", width="stretch"):
            with st.spinner("Preparing CSV export…"):
                export_view = filtered_records
                if sort_by and not export_view.empty:
                    export_view = export_view.sort_values(sort_by, ascending=not descending, na_position="last", kind="stable")
                st.session_state["deep_dive_export_bytes"] = export_view.to_csv(index=False).encode("utf-8")
                st.session_state["deep_dive_export_signature"] = (
                    len(export_view), sort_by, descending, search.strip(),
                    tuple(st.session_state.get("explorer_post_type", [])),
                    tuple(st.session_state.get("explorer_campaign", [])),
                    tuple(st.session_state.get("explorer_emotion", [])),
                    str(st.session_state.get("explorer_dates", "")),
                )
        current_signature = (
            len(filtered_records), sort_by, descending, search.strip(),
            tuple(st.session_state.get("explorer_post_type", [])),
            tuple(st.session_state.get("explorer_campaign", [])),
            tuple(st.session_state.get("explorer_emotion", [])),
            str(st.session_state.get("explorer_dates", "")),
        )
        if st.session_state.get("deep_dive_export_signature") != current_signature:
            st.session_state["deep_dive_export_bytes"] = None
        if st.session_state.get("deep_dive_export_bytes") is not None:
            left.download_button(
                "⬇️ Download filtered CSV",
                data=st.session_state["deep_dive_export_bytes"],
                file_name="sugar_instagram_filtered.csv",
                mime="text/csv",
                key="deep_dive_download_csv",
                width="stretch",
            )
        right.caption("Tip: rank by engagement rate to find posts that performed strongly relative to reach, or by total engagements to find posts with the largest interaction volume. Prepare the CSV only when you need an export.")

        if not filtered_records.empty:
            with st.expander("Inspect one record", expanded=False):
                inspect_options = display_view.index.tolist()
                row_index = st.selectbox("Choose a displayed record", inspect_options, format_func=lambda idx: f"Row {idx} · {filtered_records.loc[idx].get('post_date', 'Date unavailable')} · {filtered_records.loc[idx].get('post_type', 'Type unavailable')}", key="inspect_record")
                selected_record = filtered_records.loc[row_index]
                st.json({str(k): (None if pd.isna(v) else str(v) if isinstance(v, (pd.Timestamp,)) else v.item() if isinstance(v, np.generic) else v) for k, v in selected_record.items()})

elif active_section == "📊 Interactive Insights":
        st.subheader("Explore what is driving performance")
        st.caption("Use the filters to compare categories and follow performance over time. All metrics describe the supplied dataset, not causal impact.")
        analysis = add_filters(data, "insights")
        if analysis.empty:
            st.warning("No records match the selected filters. Widen the filters to continue.")
        else:
            weighted_er = weighted_rate(analysis, "total_engagements", "reach")
            total_reach = safe_sum(analysis, "reach")
            total_engagements = safe_sum(analysis, "total_engagements")
            total_follows = safe_sum(analysis, "follows")
            total_visits = safe_sum(analysis, "profile_visits")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Posts in scope", f"{len(analysis):,}")
            c2.metric("Weighted engagement rate", pct(weighted_er), help="Sum of engagements divided by summed reach for eligible records.")
            c3.metric("Total engagements", number(total_engagements))
            c4.metric("Summed post-level reach", number(total_reach), help="Not unique account reach.")

            st.divider()
            st.markdown("#### Category performance")
            dimensions = [c for c in ["post_type", "campaign_type", "audience_emotion", "engagement_source"] if c in analysis.columns]
            controls = st.columns([1, 1])
            dimension = controls[0].selectbox("Compare categories by", dimensions, key="insight_dimension") if dimensions else None
            metric_choice = controls[1].selectbox("Measure", ["Weighted engagement rate", "Total engagements", "Record count", "Average reach per post"], key="insight_group_metric")
            if dimension:
                grouped = analysis.groupby(dimension, dropna=False).agg(records=(dimension, "size"), engagements=("total_engagements", "sum"), reach=("reach", "sum")).reset_index()
                grouped["weighted_engagement_rate"] = grouped["engagements"] / grouped["reach"].where(grouped["reach"] > 0)
                grouped["average_reach"] = grouped["reach"] / grouped["records"].where(grouped["records"] > 0)
                metric_map = {"Weighted engagement rate": "weighted_engagement_rate", "Total engagements": "engagements", "Record count": "records", "Average reach per post": "average_reach"}
                metric_col = metric_map[metric_choice]
                grouped = grouped.sort_values(metric_col, ascending=False)
                fig = px.bar(grouped, x=dimension, y=metric_col, color=dimension, color_discrete_sequence=PALETTE, text=metric_col, title=f"{metric_choice} by {dimension.replace('_', ' ')}")
                if metric_col == "weighted_engagement_rate":
                    fig.update_yaxes(tickformat=".1%", title="Weighted engagement rate")
                    fig.update_traces(texttemplate="%{y:.1%}", textposition="outside", cliponaxis=False)
                else:
                    fig.update_yaxes(title=metric_choice)
                    fig.update_traces(texttemplate="%{y:,.3s}", textposition="outside", cliponaxis=False)
                fig.update_layout(**PLOT_LAYOUT, showlegend=False, height=390, xaxis_title=dimension.replace("_", " ").title())
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                best = grouped.iloc[0]
                if len(grouped) > 1:
                    worst = grouped.iloc[-1]
                    if metric_col == "weighted_engagement_rate":
                        gap = (float(best[metric_col]) - float(worst[metric_col])) * 100
                        st.info(f"**Takeaway:** {best[dimension]} has the highest weighted engagement rate at {best[metric_col]:.2%}, {gap:.2f} percentage points above {worst[dimension]}.")
                    else:
                        st.info(f"**Takeaway:** {best[dimension]} leads on {metric_choice.lower()} ({best[metric_col]:,.0f}). Compare sample counts before treating this as a stable pattern.")
                st.dataframe(grouped.rename(columns={dimension: "Category", "records": "Posts", "engagements": "Engagements", "reach": "Summed post reach", "weighted_engagement_rate": "Weighted engagement rate", "average_reach": "Average reach per post"}), width="stretch", hide_index=True)

            st.divider()
            st.markdown("#### Performance over time")
            if "post_date" in analysis.columns:
                monthly = analysis.dropna(subset=["post_date"]).copy()
                monthly["Month"] = monthly["post_date"].dt.to_period("M").dt.to_timestamp()
                monthly_summary = monthly.groupby("Month").agg(posts=("post_date", "size"), engagements=("total_engagements", "sum"), reach=("reach", "sum")).reset_index()
                monthly_summary["weighted_engagement_rate"] = monthly_summary["engagements"] / monthly_summary["reach"].where(monthly_summary["reach"] > 0)
                trend_choice = st.selectbox("Trend metric", ["Weighted engagement rate", "Total engagements", "Post count", "Summed post-level reach"], key="insight_trend_metric")
                trend_col = {"Weighted engagement rate": "weighted_engagement_rate", "Total engagements": "engagements", "Post count": "posts", "Summed post-level reach": "reach"}[trend_choice]
                fig = px.line(monthly_summary, x="Month", y=trend_col, markers=True, title=f"Monthly {trend_choice.lower()}", color_discrete_sequence=[PALETTE[0]])
                if trend_col == "weighted_engagement_rate": fig.update_yaxes(tickformat=".1%", title="Weighted engagement rate")
                else: fig.update_yaxes(title=trend_choice, tickformat=",.0f")
                fig.update_xaxes(tickformat="%b %Y", dtick="M1", tickangle=-35, title="Month")
                fig.update_layout(**PLOT_LAYOUT, height=370)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                with st.expander("View monthly figures"):
                    formatted = monthly_summary.copy()
                    formatted["Month"] = formatted["Month"].dt.strftime("%b %Y")
                    formatted["weighted_engagement_rate"] = formatted["weighted_engagement_rate"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "—")
                    st.dataframe(formatted, width="stretch", hide_index=True)

            st.divider()
            st.markdown("#### Engagement actions and conversion proxies")
            left, right = st.columns(2, gap="large")
            with left:
                action_cols = [c for c in ["likes", "comments", "shares", "saves"] if c in analysis.columns]
                if action_cols:
                    mix = pd.DataFrame({"Action": action_cols, "Interactions": [safe_sum(analysis, c) for c in action_cols]}).sort_values("Interactions", ascending=False)
                    fig = px.pie(mix, names="Action", values="Interactions", hole=0.58, color_discrete_sequence=PALETTE, title="Share of engagement actions")
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    fig.update_layout(**PLOT_LAYOUT, height=360, legend_title_text="Action")
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            with right:
                if pd.notna(total_visits) and total_visits > 0 and pd.notna(total_follows):
                    proxy = total_follows / total_visits
                    fig = go.Figure(go.Indicator(mode="number+gauge", value=proxy * 100, number={"suffix": "%", "valueformat": ".2f"}, title={"text": "Profile Visit-to-Follow Rate<br><sup>Aggregate proxy</sup>"}, gauge={"axis": {"range": [0, max(100, min(100, proxy * 100 * 1.2))]}, "bar": {"color": PALETTE[1]}, "steps": [{"range": [0, 25], "color": "#392535"}, {"range": [25, 50], "color": "#493049"}, {"range": [50, 100], "color": "#2E4650"}]}))
                    fig.update_layout(**PLOT_LAYOUT, height=360)
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                    st.caption("Follows ÷ profile visits × 100. Aggregate proxy only: the dataset cannot link individual visits to specific follows or establish causation.")
                else:
                    st.info("Profile visits and follows are not sufficient to calculate the proxy for these filters.")

elif active_section == "🛡️ Data Quality & Methodology":
        st.subheader("Data quality & methodology")
        st.caption("Transparent checks help distinguish data errors, unusual values, and limitations in interpretation.")

        quality_rows = [
            ("Rows", quality.get("rows", len(df))),
            ("Columns", quality.get("columns", len(df.columns))),
            ("Missing cells", quality.get("missing_cells", int(df.isna().sum().sum()))),
            ("Exact duplicate rows", quality.get("duplicate_rows", int(df.duplicated().sum()))),
        ]
        metric_cols = st.columns(4)
        for column, (label, value) in zip(metric_cols, quality_rows):
            column.metric(label, f"{value:,.0f}" if isinstance(value, (int, float, np.integer, np.floating)) and pd.notna(value) else str(value))

        summary_rows = [
            {"Check": str(key).replace("_", " ").strip().title(), "Result": str(value)}
            for key, value in quality.items() if key != "flags"
        ]
        with st.expander("Validation summary", expanded=False):
            if summary_rows:
                st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)
            else:
                st.info("No summary checks were returned.")

        st.markdown("#### Derived metric checks")
        metric_checks = []
        if all(c in data.columns for c in ["likes", "comments", "shares", "saves"]):
            expected = data[["likes", "comments", "shares", "saves"]].sum(axis=1, min_count=4)
            if "total_engagements" in f.columns:
                actual = pd.to_numeric(f["total_engagements"], errors="coerce")
                comparable = actual.notna() & expected.notna()
                mismatch = comparable & ~np.isclose(actual.fillna(0), expected.fillna(0), rtol=1e-9, atol=1e-9)
                metric_checks.append({"Check": "Total engagements = likes + comments + shares + saves", "Rows checked": int(comparable.sum()), "Mismatches": int(mismatch.sum()), "Status": "Pass" if not mismatch.any() else "Review"})
            if "reach" in data.columns and "engagement_rate" in f.columns:
                reach_values = pd.to_numeric(data["reach"], errors="coerce")
                actual_rate = pd.to_numeric(f["engagement_rate"], errors="coerce")
                expected_rate = expected / reach_values.where(reach_values > 0)
                comparable = actual_rate.notna() & expected_rate.notna()
                mismatch = comparable & ~np.isclose(actual_rate.fillna(0), expected_rate.fillna(0), rtol=1e-7, atol=1e-9)
                metric_checks.append({"Check": "Engagement rate = total engagements / reach (reach > 0)", "Rows checked": int(comparable.sum()), "Mismatches": int(mismatch.sum()), "Status": "Pass" if not mismatch.any() else "Review"})
        if metric_checks:
            st.dataframe(pd.DataFrame(metric_checks), width="stretch", hide_index=True)
        else:
            st.info("The source data does not contain all columns needed for these checks.")

        st.markdown("#### Statistical outlier screening (IQR)")
        st.caption("Use the metric selector to focus on one distribution. The standard IQR fences are statistical thresholds, not business validity rules.")
        numeric_candidates = [c for c in ["impressions", "reach", "likes", "comments", "shares", "saves", "profile_visits", "follows", "total_engagements", "engagement_rate"] if c in data.columns]
        if numeric_candidates:
            selected_metric = st.selectbox("Metric to inspect", numeric_candidates, key="iqr_metric")
            values = pd.to_numeric(data[selected_metric], errors="coerce").dropna()
            if not values.empty:
                q1, q3 = float(values.quantile(.25)), float(values.quantile(.75))
                iqr = q3 - q1
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                flagged_mask = (pd.to_numeric(data[selected_metric], errors="coerce") < lower) | (pd.to_numeric(data[selected_metric], errors="coerce") > upper)
                flagged_count = int(flagged_mask.sum())
                a, b, c, d = st.columns(4)
                if selected_metric.endswith("rate"):
                    a.metric("Q1", pct(q1))
                    b.metric("Q3", pct(q3))
                else:
                    a.metric("Q1", f"{q1:,.2f}")
                    b.metric("Q3", f"{q3:,.2f}")
                c.metric("Flagged rows", f"{flagged_count:,}")
                d.metric("Flagged share", f"{flagged_count / len(values):.2%}")
                fig = go.Figure(go.Histogram(
                    x=values.to_numpy(),
                    nbinsx=30,
                    marker_color=PALETTE[2],
                    opacity=0.9,
                    name=selected_metric,
                ))
                fig.update_layout(title=f"Distribution of {selected_metric.replace('_', ' ')}")
                fig.add_vline(x=lower, line_dash="dash", line_color=PALETTE[0], annotation_text="Lower IQR fence")
                fig.add_vline(x=upper, line_dash="dash", line_color=PALETTE[3], annotation_text="Upper IQR fence")
                fig.add_vline(x=q1, line_dash="dot", line_color=PALETTE[1], annotation_text="Q1")
                fig.add_vline(x=q3, line_dash="dot", line_color=PALETTE[4], annotation_text="Q3")
                fig.update_layout(**PLOT_LAYOUT, height=390, xaxis_title=selected_metric.replace("_", " ").title(), yaxis_title="Number of records", bargap=0.06)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                st.caption(f"IQR fences: {lower:,.4f} to {upper:,.4f}. The X-axis shows metric values; the Y-axis shows record counts. For count metrics, a negative lower fence is mathematical only.")
                if flagged_count:
                    flagged_view = data.loc[flagged_mask]
                    keep = [c for c in ["post_date", "post_type", "campaign_type", "hashtags", selected_metric, "reach", "total_engagements", "engagement_rate"] if c in flagged_view.columns]
                    st.markdown("##### Records flagged for review")
                    st.dataframe(flagged_view[keep].sort_values(selected_metric, ascending=False), width="stretch", hide_index=True, height=300)
                    st.download_button("Download flagged records (CSV)", dataframe_csv(flagged_view), file_name=f"iqr_flagged_{selected_metric}.csv", mime="text/csv", key="download_iqr_flags")
                else:
                    st.success("No records are outside the standard IQR fences for this metric.")
        else:
            st.info("No supported numeric metrics were available for outlier screening.")

        st.markdown("#### Metric definitions")
        st.markdown(
            """
            - **Total engagements:** likes + comments + shares + saves.
            - **Post engagement rate:** total engagements ÷ reach, where reach is greater than zero.
            - **Weighted engagement rate:** total engagements ÷ total reach across eligible records.
            - **Profile-visit rate proxy:** profile visits ÷ reach.
            - **Follow-per-visit proxy:** follows ÷ profile visits, where profile visits are greater than zero.
            - **Summed post-level reach:** sum of reach values across records; not unique account reach.
            """
        )
        st.markdown("#### Important caveats")
        st.markdown(
            """
            - Data source, collection method, account identity, row grain, and sampling strategy could not be verified from the supplied files; official Sugar Cosmetics account performance therefore remains unconfirmed.
            - No post ID, caption, posting time, follower count, demographic attributes, spend, sales or revenue fields are provided.
            - The near-even distribution across post types and campaign types, plus 136.612 records per calendar day, requires row-grain and sampling confirmation before generalizing. Demographic fairness and business ROI also cannot be assessed because the required fields are absent.
            - Higher engagement or correlation does not establish causation.
            - Grouped hashtag results overlap when a record contains multiple hashtags.
            """
        )

        st.markdown("#### Validation flags")
        flags = quality.get("flags", [])
        flags_df = flags.copy() if isinstance(flags, pd.DataFrame) else pd.DataFrame(flags)
        if not flags_df.empty:
            st.dataframe(flags_df, width="stretch", hide_index=True)
        else:
            st.success("No issues were reported by the current validation rules. This does not prove the data is authentic or free from every possible issue.")

st.divider()
st.caption("Sugar Cosmetics Instagram Performance Analytics · Streamlit · Descriptive analysis of the supplied dataset.")
