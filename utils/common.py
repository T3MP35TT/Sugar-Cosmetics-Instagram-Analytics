
"""Shared initialization and page header for the Sugar Cosmetics dashboard."""

from pathlib import Path
import sys
import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from analytics import (
    add_features,
    hashtag_table,
    load_data,
    summarize_data,
    validate_data,
    weekday_table,
)

from utils.theme import (
    SUGAR_BORDER,
    SUGAR_CHART,
    SUGAR_DARK,
    SUGAR_INK,
    SUGAR_MUTED,
    SUGAR_PALE,
    SUGAR_PINK,
    SUGAR_PLUM,
    SUGAR_SURFACE,
    apply_theme,
)


PAGE_SUBTITLES = {
    "Home": "Project overview, tools, and setup.",
    "Executive Overview": "Performance at a glance, with key metrics and trends.",
    "Content Performance": "Compare formats and identify content associated with stronger engagement.",
    "Posting Strategy": "Explore posting frequency, monthly patterns, and weekday performance.",
    "Hashtag Intelligence": "Examine hashtag usage and its association with engagement.",
    "Audience & Conversion": "Explore reach, profile visits, and follow-related metrics.",
    "Audience Conversion": "Explore reach, profile visits, and follow-related metrics.",
    "Engagement Funnel": "Understand the relationship between exposure and interactions.",
    "Deep-Dive Explorer": "Filter, search, inspect, and export the underlying records.",
    "Deep Dive Explorer": "Filter, search, inspect, and export the underlying records.",
    "Data Quality & Methodology": "Review data validation, metric definitions, and analytical limitations.",
    "Data Quality Methodology": "Review data validation, metric definitions, and analytical limitations.",
    "Strategic Recommendations": "Translate descriptive findings into measurable experiments.",
}


def render_page_header(page_name):
    """Render logo and page title together inside one branded header."""

    logo_path = ROOT / "images" / "sugar_logo.png"
    subtitle = PAGE_SUBTITLES.get(
        page_name,
        "Instagram performance analytics and insights.",
    )

    safe_page_name = html.escape(str(page_name))
    safe_subtitle = html.escape(str(subtitle))

    st.markdown(
        """
        <style>
        .sugar-page-header {
            box-sizing: border-box;
            width: 100%;
            display: flex;
            align-items: center;
            gap: 20px;
            background: linear-gradient(120deg, #35232f 0%, #291a25 72%, #21151e 100%);
            border: 1px solid #634257;
            border-radius: 15px;
            padding: 24px 28px 22px 28px;
            margin: 0 0 22px 0;
            box-shadow: 0 5px 18px rgba(18, 8, 15, 0.12);
        }
        .sugar-header-logo {
            width: 66px;
            height: 66px;
            min-width: 66px;
            object-fit: contain;
            display: block;
            border-radius: 12px;
        }
        .sugar-header-logo-fallback {
            width: 58px;
            height: 58px;
            min-width: 58px;
            border-radius: 12px;
            background: #e84f87;
            color: #fff8fb;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 29px;
            font-weight: 800;
        }
        .sugar-header-content {
            min-width: 0;
            flex: 1;
        }
        .sugar-brand-line {
            color: #f3a6c4;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin: 0 0 12px 0;
        }
        .sugar-page-title {
            color: #fff8fb !important;
            font-family: inherit !important;
            font-size: 2.45rem !important;
            line-height: 1.14 !important;
            font-weight: 780 !important;
            letter-spacing: -0.045em !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .sugar-page-subtitle {
            color: #e8d7e1 !important;
            font-family: inherit !important;
            font-size: 1rem !important;
            margin: 8px 0 0 0 !important;
            padding: 0 !important;
        }
        .sugar-header-accent {
            width: 48px;
            height: 4px;
            background: #e84f87;
            border-radius: 5px;
            margin-top: 17px;
        }
        @media (max-width: 640px) {
            .sugar-page-header {
                gap: 13px;
                padding: 18px;
            }
            .sugar-header-logo {
                width: 46px;
                height: 46px;
                min-width: 46px;
            }
            .sugar-header-logo-fallback {
                width: 44px;
                height: 44px;
                min-width: 44px;
            }
            .sugar-page-title {
                font-size: 1.8rem !important;
            }
            .sugar-brand-line {
                font-size: 0.62rem;
                letter-spacing: 0.07em;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if logo_path.is_file():
        import base64

        with open(logo_path, "rb") as logo_file:
            encoded_logo = base64.b64encode(logo_file.read()).decode("ascii")

        logo_html = (
            f'<img class="sugar-header-logo" '
            f'src="data:image/png;base64,{encoded_logo}" '
            f'alt="SUGAR Cosmetics logo">'
        )
    else:
        logo_html = '<div class="sugar-header-logo-fallback">S</div>'

    st.markdown(
        f"""
        <div class="sugar-page-header">
            {logo_html}
            <div class="sugar-header-content">
                <div class="sugar-brand-line">
                    SUGAR COSMETICS&nbsp;&nbsp; / &nbsp;&nbsp;
                    INSTAGRAM PERFORMANCE ANALYTICS
                </div>
                <h1 class="sugar-page-title">{safe_page_name}</h1>
                <p class="sugar-page-subtitle">{safe_subtitle}</p>
                <div class="sugar-header-accent"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Preparing dashboard data…", max_entries=2)
def _load_project_bundle(data_path: str, modified_ns: int, file_size: int):
    """Load, validate and feature-engineer the dataset once per file version.

    The file's path, modification timestamp and size form the cache key, so
    updates to the source dataset automatically invalidate the cached bundle.
    """
    source = Path(data_path)
    raw_data = load_data(source)
    quality_report = validate_data(raw_data)
    featured_data = add_features(raw_data)
    return raw_data, quality_report, featured_data


def initialize(page_name):
    """Configure the page, display the shared header, load data and define helpers."""

    st.set_page_config(
        page_title=f"SUGAR | {page_name}",
        page_icon="💄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_theme()
    render_page_header(page_name)

    csv_path = ROOT / "data" / "sugar_cosmetics_instagram_data.csv"
    excel_path = ROOT / "data" / "sugar_cosmetics_instagram_data.xlsx"
    data_path = csv_path if csv_path.exists() else excel_path

    if not data_path.exists():
        st.error("Dataset not found in the project's data folder.")
        st.stop()

    try:
        stat = data_path.stat()
        raw, quality, df = _load_project_bundle(
            str(data_path),
            stat.st_mtime_ns,
            stat.st_size,
        )
    except Exception as exc:
        st.error(f"Could not prepare the project dataset: {exc}")
        st.stop()

    # Pages should treat the shared dataframe as read-only and create a subset
    # only when applying filters. Avoid copying all 50k rows on every page load.
    filtered = df

    def kpis(data):
        total_engagements = data["total_engagements"].sum()
        reach = data["reach"].sum()
        follows = data["follows"].sum()

        columns = st.columns(5)
        columns[0].metric("Records analysed", f"{len(data):,}", help="A unique post identifier is not available, so record count is not verified post count.")
        columns[1].metric("Total engagements", f"{total_engagements:,.0f}")
        columns[2].metric("Cumulative reach*", f"{reach:,.0f}")
        columns[3].metric(
            "Weighted engagement rate",
            f"{total_engagements / reach:.2%}" if reach else "—",
        )
        columns[4].metric("Follows", f"{follows:,.0f}")

        st.caption(
            "*Sum of post-level reach; not unique account-level reach. "
            "Engagement rate = (likes + comments + shares + saves) / reach."
        )

    def page_kpis(active_page, data):
        count = len(data)
        reach = data["reach"].sum()
        impressions = data["impressions"].sum()
        engagements = data["total_engagements"].sum()
        likes = data["likes"].sum()
        comments = data["comments"].sum()
        shares = data["shares"].sum()
        saves = data["saves"].sum()
        visits = data["profile_visits"].sum()
        follows = data["follows"].sum()

        if active_page == "Content Performance":
            averages = data.groupby("post_type")["total_engagements"].mean()
            top_format = averages.idxmax() if not averages.empty else "—"
            values = [
                ("Records analysed", f"{count:,}"),
                ("Average likes", f"{data['likes'].mean():,.1f}"),
                ("Average comments", f"{data['comments'].mean():,.1f}"),
                ("Average saves", f"{data['saves'].mean():,.1f}"),
                ("Top format by avg. engagement", str(top_format)),
            ]

        elif active_page == "Posting Strategy":
            monthly = data.assign(
                _month=data["post_date"].dt.to_period("M")
            ).groupby("_month").size()
            weekdays = weekday_table(data)
            best_day = (
                weekdays.sort_values(
                    "weighted_engagement_rate", ascending=False
                ).iloc[0]["weekday"]
                if not weekdays.empty
                else "—"
            )
            values = [
                (
                    "Average records / month",
                    f"{monthly.mean():,.0f}" if not monthly.empty else "—",
                ),
                (
                    "Most active month",
                    str(monthly.idxmax()) if not monthly.empty else "—",
                ),
                ("Best weekday by weighted rate", str(best_day)),
                (
                    "Active weekdays",
                    f"{data['post_date'].dt.day_name().nunique():,}",
                ),
                (
                    "Weighted engagement rate",
                    f"{engagements / reach:.2%}" if reach else "—",
                ),
            ]

        elif active_page == "Hashtag Intelligence":
            hashtags = hashtag_table(data)
            top_hashtag = (
                str(hashtags.iloc[0]["hashtag"]) if not hashtags.empty else "—"
            )
            top_rate = (
                hashtags.iloc[0]["weighted_engagement_rate"]
                if not hashtags.empty
                else None
            )
            values = [
                ("Hashtags identified", f"{len(hashtags):,}"),
                ("Top hashtag", top_hashtag),
                (
                    "Top hashtag engagement rate",
                    f"{top_rate:.2%}" if top_rate is not None else "—",
                ),
                ("Records analysed", f"{count:,}"),
                ("Total engagements", f"{engagements:,.0f}"),
            ]

        elif active_page in ("Audience & Conversion", "Audience Conversion"):
            values = [
                ("Profile visits", f"{visits:,.0f}"),
                ("Follows", f"{follows:,.0f}"),
                ("Visits / reach", f"{visits / reach:.2%}" if reach else "—"),
                (
                    "Follows / visits",
                    f"{follows / visits:.2%}" if visits else "—",
                ),
                ("Follows / reach", f"{follows / reach:.2%}" if reach else "—"),
            ]

        elif active_page == "Engagement Funnel":
            values = [
                ("Impressions", f"{impressions:,.0f}"),
                ("Reach (summed)", f"{reach:,.0f}"),
                ("Likes", f"{likes:,.0f}"),
                ("Comments", f"{comments:,.0f}"),
                ("Shares + saves", f"{shares + saves:,.0f}"),
            ]

        elif active_page in ("Deep-Dive Explorer", "Deep Dive Explorer"):
            values = [
                ("Matching records", f"{count:,}"),
                ("Total engagements", f"{engagements:,.0f}"),
                ("Total reach (summed)", f"{reach:,.0f}"),
                (
                    "Average engagement rate",
                    f"{data['engagement_rate'].mean():.2%}",
                ),
                (
                    "Date span",
                    f"{data['post_date'].min():%d %b %Y} – "
                    f"{data['post_date'].max():%d %b %Y}",
                ),
            ]

        elif active_page == "Strategic Recommendations":
            totals_by_type = data.groupby("post_type")["total_engagements"].sum()
            best_type = (
                totals_by_type.idxmax() if not totals_by_type.empty else "—"
            )
            values = [
                ("Records in scope", f"{count:,}"),
                (
                    "Weighted engagement rate",
                    f"{engagements / reach:.2%}" if reach else "—",
                ),
                ("Total saves", f"{saves:,.0f}"),
                ("Total shares", f"{shares:,.0f}"),
                ("Format with most engagements", str(best_type)),
            ]

        else:
            return

        columns = st.columns(len(values))
        for column, (label, value) in zip(columns, values):
            column.metric(label, value)

        st.divider()

    def bar(data, x, y, title, color=None, labels=None, orientation=None):
        figure = px.bar(
            data,
            x=x,
            y=y,
            color=color,
            title=title,
            labels=labels,
            orientation=orientation,
            color_discrete_sequence=[
                SUGAR_PINK,
                "#F3A6C4",
                "#B66B91",
                "#FFFFFF",
                SUGAR_PLUM,
            ],
            template="sugar",
        )

        figure.update_layout(
            paper_bgcolor=SUGAR_PALE,
            plot_bgcolor=SUGAR_CHART,
            font_color=SUGAR_INK,
            margin=dict(l=10, r=10, t=55, b=10),
            legend_title_text="",
        )

        st.plotly_chart(figure, width="stretch")

    return {
        "pd": pd,
        "st": st,
        "px": px,
        "go": go,
        "ROOT": ROOT,
        "SUGAR_PINK": SUGAR_PINK,
        "SUGAR_PLUM": SUGAR_PLUM,
        "SUGAR_PALE": SUGAR_PALE,
        "SUGAR_SURFACE": SUGAR_SURFACE,
        "SUGAR_BORDER": SUGAR_BORDER,
        "SUGAR_DARK": SUGAR_DARK,
        "SUGAR_INK": SUGAR_INK,
        "SUGAR_MUTED": SUGAR_MUTED,
        "SUGAR_CHART": SUGAR_CHART,
        "load_data": load_data,
        "validate_data": validate_data,
        "add_features": add_features,
        "summarize_data": summarize_data,
        "hashtag_table": hashtag_table,
        "weekday_table": weekday_table,
        "raw": raw,
        "quality": quality,
        "df": df,
        "f": filtered,
        "page": page_name,
        "kpis": kpis,
        "page_kpis": page_kpis,
        "bar": bar,
    }
