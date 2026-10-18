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

strategy_source = f.copy()
strategy_source["post_date"] = pd.to_datetime(strategy_source["post_date"], errors="coerce")
with st.container(border=True):
    st.subheader("Posting strategy filters")
    filter_cols = st.columns(3)
    usable_dates = strategy_source["post_date"].dropna()
    if usable_dates.empty:
        st.warning("No valid dates are available for posting analysis.")
        st.stop()
    date_min, date_max = usable_dates.min().date(), usable_dates.max().date()
    selected_dates = filter_cols[0].date_input(
        "Date range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
        key="posting_strategy_date_range",
    )
    available_types = sorted(strategy_source["post_type"].dropna().astype(str).unique())
    selected_types = filter_cols[1].multiselect(
        "Post format",
        available_types,
        default=available_types,
        key="posting_strategy_post_types",
    )
    available_campaigns = sorted(strategy_source["campaign_type"].dropna().astype(str).unique())
    selected_campaigns = filter_cols[2].multiselect(
        "Campaign",
        available_campaigns,
        default=available_campaigns,
        key="posting_strategy_campaigns",
    )

f = strategy_source
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    f = f[f["post_date"].dt.date.between(selected_dates[0], selected_dates[1])]
f = f[f["post_type"].astype(str).isin(selected_types)]
f = f[f["campaign_type"].astype(str).isin(selected_campaigns)]
render_sidebar_summary("Posting Strategy", f)
if f.empty:
    st.warning("No records match these filters. Widen the date range or select more formats or campaigns.")
    st.stop()

with st.container(border=True):
    st.subheader("Selected scope summary")
    page_kpis("Posting Strategy", f)

# Monthly posting cadence
with st.container(border=True):
    st.subheader("Monthly cadence and engagement")
    st.caption(
        "Monthly row counts describe the supplied records. Weighted engagement rate is summed engagements divided by summed reach; "
        "it is not an estimate of publishing frequency until the row grain is verified."
    )
    monthly_source = f.dropna(subset=["post_date"]).copy()
    if not monthly_source.empty:
        st.caption(
            f"Date coverage: {monthly_source['post_date'].min():%d %b %Y} to "
            f"{monthly_source['post_date'].max():%d %b %Y} · "
            f"{monthly_source['post_date'].dt.to_period('M').nunique()} observed months · "
            f"{len(monthly_source):,} dated records."
        )
    monthly = (
        monthly_source.assign(month=monthly_source["post_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(
            records=("post_date", "size"),
            reach=("reach", lambda values: values.sum(min_count=1)),
            engagements=("total_engagements", lambda values: values.sum(min_count=1)),
        )
        .sort_values("month")
    )
    if not monthly.empty:
        full_months = pd.date_range(monthly["month"].min(), monthly["month"].max(), freq="MS")
        monthly = (
            monthly.set_index("month")
            .reindex(full_months)
            .rename_axis("month")
            .reset_index()
        )
        monthly["records"] = monthly["records"].fillna(0).astype(int)
    monthly["weighted_engagement_rate"] = monthly["engagements"] / monthly["reach"].where(monthly["reach"] > 0)

    if not monthly.empty:
        monthly_left, monthly_right = st.columns(2, gap="large")
        with monthly_left:
            fig_monthly = px.area(
                monthly,
                x="month",
                y="records",
                markers=True,
                title="Record volume by month",
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
                title=dict(text="Record volume by month", x=0.02, xanchor="left"),
                margin=dict(l=15, r=20, t=65, b=15),
                hovermode="x unified",
            )
            st.plotly_chart(fig_monthly, width="stretch")

        with monthly_right:
            rate_data = monthly.dropna(subset=["weighted_engagement_rate"])
            if not rate_data.empty:
                fig_monthly_rate = px.line(
                    rate_data,
                    x="month",
                    y="weighted_engagement_rate",
                    markers=True,
                    title="Weighted engagement rate by month",
                    labels={"month": "Month", "weighted_engagement_rate": "Weighted rate"},
                    color_discrete_sequence=["#9b4d78"],
                )
                fig_monthly_rate.update_traces(
                    line=dict(color="#9b4d78", width=3),
                    marker=dict(size=8, color="#f6a6c1", line=dict(color="#fff0f6", width=1.5)),
                    customdata=rate_data[["records", "reach", "engagements"]],
                    hovertemplate=(
                        "<b>%{x|%b %Y}</b><br>Weighted rate: %{y:.2%}"
                        "<br>Records: %{customdata[0]:,.0f}"
                        "<br>Summed reach: %{customdata[1]:,.0f}"
                        "<br>Engagements: %{customdata[2]:,.0f}<extra></extra>"
                    ),
                )
                fig_monthly_rate.update_layout(
                    template="sugar",
                    title=dict(text="Weighted engagement rate by month", x=0.02, xanchor="left"),
                    yaxis_tickformat=".1%",
                    yaxis_rangemode="tozero",
                    margin=dict(l=15, r=20, t=65, b=15),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_monthly_rate, width="stretch")
            else:
                st.info("Monthly weighted engagement rates are unavailable because reach is zero or missing.")

        peak_month = monthly.loc[monthly["records"].idxmax()]
        low_month = monthly.loc[monthly["records"].idxmin()]
        valid_monthly_rates = monthly.dropna(subset=["weighted_engagement_rate"])
        takeaway = (
            f"Record volume was highest in <strong>{peak_month['month']:%B %Y}</strong> "
            f"({peak_month['records']:,} records) and was lowest in "
            f"<strong>{low_month['month']:%B %Y}</strong> ({low_month['records']:,} records). "
            + (
                f"The highest monthly weighted engagement rate was {valid_monthly_rates.loc[valid_monthly_rates['weighted_engagement_rate'].idxmax(), 'weighted_engagement_rate']:.2%}. "
                if not valid_monthly_rates.empty
                else "Monthly engagement rate could not be calculated. "
            )
            + "Compare volume and rate together; neither shows that cadence caused engagement changes."
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

with st.container(border=True):
    st.subheader("Daily record cadence")
    st.caption(
        "Daily counts include zero-record dates inside the selected date span. A seven-day rolling mean helps reveal broad volume changes; "
        "these are record counts, not confirmed post counts."
    )
    dated_records = f.dropna(subset=["post_date"]).copy()
    daily_counts = dated_records.groupby(dated_records["post_date"].dt.normalize()).size()
    calendar_days = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily = daily_counts.reindex(calendar_days, fill_value=0).rename("records").to_frame()
    daily["seven_day_mean"] = daily["records"].rolling(7, min_periods=1).mean()
    daily_kpis = st.columns(4)
    daily_kpis[0].metric("Calendar days in scope", f"{len(daily):,}")
    daily_kpis[1].metric("Dates with records", f"{int(daily['records'].gt(0).sum()):,}")
    daily_kpis[2].metric("Zero-record dates", f"{int(daily['records'].eq(0).sum()):,}")
    daily_kpis[3].metric("Peak records in one date", f"{int(daily['records'].max()):,}")
    daily_fig = go.Figure()
    daily_fig.add_trace(
        go.Scatter(
            x=daily.index,
            y=daily["records"],
            mode="lines",
            name="Records per date",
            line=dict(color="#e84f87", width=1.4),
            opacity=0.55,
            hovertemplate="%{x|%d %b %Y}<br>Records: %{y:,.0f}<extra></extra>",
        )
    )
    daily_fig.add_trace(
        go.Scatter(
            x=daily.index,
            y=daily["seven_day_mean"],
            mode="lines",
            name="7-day mean",
            line=dict(color="#f6a6c1", width=3),
            hovertemplate="%{x|%d %b %Y}<br>7-day mean: %{y:.1f}<extra></extra>",
        )
    )
    daily_fig.update_layout(
        template="sugar",
        title=dict(text="Records by date with seven-day rolling mean", x=0.02, xanchor="left"),
        xaxis_title="Date",
        yaxis_title="Records (row count)",
        yaxis_rangemode="tozero",
        hovermode="x unified",
        margin=dict(l=15, r=20, t=65, b=15),
        legend_title_text="",
    )
    st.plotly_chart(daily_fig, width="stretch")

st.divider()

with st.container(border=True):
    st.subheader("Weekday performance")
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
        weekday_record_total = weekdays["records"].sum()
        weekdays["record_share"] = weekdays["records"] / weekday_record_total if weekday_record_total else float("nan")
        overall_reach = pd.to_numeric(f["reach"], errors="coerce")
        overall_engagements = pd.to_numeric(f["total_engagements"], errors="coerce")
        overall_eligible = overall_reach.gt(0) & overall_engagements.notna()
        overall_rate = (
            overall_engagements.loc[overall_eligible].sum() / overall_reach.loc[overall_eligible].sum()
            if overall_eligible.any()
            else float("nan")
        )
        weekdays["difference_from_scope_pp"] = (weekdays["weighted_engagement_rate"] - overall_rate) * 100

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
                customdata=chart_weekdays[["records", "reach", "engagements"]],
                hovertemplate=(
                    "<b>%{x}</b><br>Weighted engagement rate: %{y:.2%}"
                    "<br>Records: %{customdata[0]:,.0f}"
                    "<br>Summed reach: %{customdata[1]:,.0f}"
                    "<br>Engagements: %{customdata[2]:,.0f}<extra></extra>"
                ),
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
                f"<strong>{best_day['weekday']}</strong> has the highest observed weighted rate "
                f"({best_day['weighted_engagement_rate']:.2%}; {best_day['records']:,} records), while "
                f"<strong>{worst_day['weekday']}</strong> has the lowest "
                f"({worst_day['weighted_engagement_rate']:.2%}; {worst_day['records']:,} records). "
                f"That is {((best_day['weighted_engagement_rate'] - overall_rate) * 100):+.2f} pp versus the selected-scope rate. "
                "Check sample sizes and campaign mix, then test weekday choices before changing the calendar."
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
    for column in ["weighted_engagement_rate", "average_engagement_rate", "record_share"]:
        if column in display_weekdays.columns:
            display_weekdays[column] = display_weekdays[column].map(
                lambda value: f"{value:.2%}" if pd.notna(value) else "—"
            )
    if "difference_from_scope_pp" in display_weekdays.columns:
        display_weekdays["difference_from_scope_pp"] = display_weekdays["difference_from_scope_pp"].map(
            lambda value: f"{value:+.2f}" if pd.notna(value) else "—"
        )
    for column in ["records", "reach", "engagements"]:
        if column in display_weekdays.columns:
            display_weekdays[column] = display_weekdays[column].map(
                lambda value: f"{value:,.0f}" if pd.notna(value) else "—"
            )
    display_weekdays = display_weekdays.rename(
        columns={
            "weekday": "Weekday",
            "records": "Records",
            "reach": "Summed reach",
            "engagements": "Engagements",
            "average_engagement_rate": "Mean record rate",
            "weighted_engagement_rate": "Weighted engagement rate",
            "record_share": "Share of records",
            "difference_from_scope_pp": "Difference vs scope (pp)",
        }
    )
    st.dataframe(display_weekdays, width="stretch", hide_index=True)

    st.info(
        "The dataset contains post dates but no posting-time field. It can support weekday analysis, "
        "but it cannot establish the best hour of day to publish."
    )

with st.container(border=True):
    st.subheader("How to use these patterns")
    st.markdown(
        """
        - Compare monthly record volume with weighted engagement rate; a busy month is not necessarily a more effective month.
        - Treat the highest weekday as a test candidate. Keep format, campaign goal, audience, paid support, and measurement window comparable.
        - Preselect one primary outcome and a useful minimum lift, then compare randomized or carefully matched publishing slots before changing the calendar.
        - Bring post IDs, publication timestamps, and attributed outcomes into the next data refresh to verify cadence and business value.
        """
    )

st.divider()
st.caption(
    "SUGAR Cosmetics Instagram Performance Analytics · Results reflect the supplied dataset "
    "and active global filters. Dataset provenance is not independently verified."
)
