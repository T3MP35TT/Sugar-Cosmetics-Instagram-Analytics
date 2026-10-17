from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize

context = initialize("Home")
globals().update(context)

# Project introduction
st.markdown(
    """
    <div style="
        background: linear-gradient(120deg, #35232f 0%, #291a25 68%, #21151e 100%);
        border: 1px solid #634257; border-radius: 15px;
        padding: 24px 26px; margin: 0 0 18px 0;">
        <div style="color:#f3a6c4;font-size:0.72rem;font-weight:800;
                    letter-spacing:0.14em;text-transform:uppercase;margin-bottom:9px;">
            SUGAR COSMETICS · PROJECT HOME
        </div>
        <div style="color:#fff8fb;font-size:1.75rem;font-weight:800;
                    line-height:1.2;margin-bottom:10px;">
            Instagram Performance Analytics
        </div>
        <div style="color:#eadde5;font-size:1rem;line-height:1.6;">
            Explore content performance, engagement patterns, campaign activity,
            hashtag associations and audience conversion proxies in one place.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# A compact dataset snapshot, based on the loaded data
data = df
date_col = "post_date" if "post_date" in data.columns else None
total_records = len(data)
date_span = "Not available"
if date_col and not data.empty:
    dates = pd.to_datetime(data[date_col], errors="coerce").dropna()
    if not dates.empty:
        date_span = f"{dates.min():%d %b %Y} – {dates.max():%d %b %Y}"

kpi_cols = st.columns(3)
kpi_cols[0].metric("Records available", f"{total_records:,}")
kpi_cols[1].metric("Date coverage", date_span)
kpi_cols[2].metric(
    "Analysis areas",
    "9 pages",
    help="Executive overview, content, posting, hashtags, audience, funnel, explorer, data quality and recommendations.",
)
st.markdown("")

left, right = st.columns([1.35, 1], gap="medium")

with left:
    with st.container(border=True):
        st.caption("PROJECT OVERVIEW")
        st.subheader("What you can investigate")
        st.markdown(
            """
            **Content & publishing**  
            Compare post formats, campaign types, posting cadence and weekday patterns.

            **Engagement & discovery**  
            Explore engagement rates, hashtag associations and recorded audience-emotion labels.

            **Audience outcomes**  
            Compare reach, profile visits and follows as aggregate conversion proxies.

            **Decision support**  
            Inspect individual records, review data quality and turn findings into testable experiments.
            """
        )

    with st.container(border=True):
        st.caption("GETTING STARTED")
        st.subheader("Run the dashboard")
        st.markdown("**1 · Install dependencies**")
        st.code("python -m pip install -r requirements.txt", language="powershell")
        st.markdown("**2 · Check the dataset**")
        st.write("Keep the supplied CSV or Excel dataset in the project's `data` folder.")
        st.markdown("**3 · Launch the app**")
        st.code("streamlit run app.py", language="powershell")
        st.caption(
            "When Streamlit starts, open the local URL printed in your terminal. "
            "Use the sidebar to move between analytics pages."
        )

with right:
    with st.container(border=True):
        st.caption("PROJECT TOOLKIT")
        st.subheader("Tools used")
        tech = st.columns(2)
        tech[0].markdown("**Python**\n\nData processing")
        tech[1].markdown("**Streamlit**\n\nInteractive app")
        tech[0].markdown("**Pandas**\n\nData preparation")
        tech[1].markdown("**Plotly**\n\nInteractive charts")
        st.divider()
        st.markdown("**Analysis workflow**")
        st.markdown(
            """
            <div style="border-left:3px solid #e84f87;padding:2px 0 3px 12px;margin:10px 0;">
              <b>01 · Explore</b><br><span style="color:#cdbbc7;">Review headline metrics and trends.</span>
            </div>
            <div style="border-left:3px solid #b66b91;padding:2px 0 3px 12px;margin:10px 0;">
              <b>02 · Compare</b><br><span style="color:#cdbbc7;">Filter formats, campaigns and audience labels.</span>
            </div>
            <div style="border-left:3px solid #f3a6c4;padding:2px 0 3px 12px;margin:10px 0;">
              <b>03 · Act</b><br><span style="color:#cdbbc7;">Use findings to shape measurable experiments.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.caption("PROJECT STRUCTURE")
        st.subheader("Where things live")
        st.markdown(
            """
            - `pages/` — individual analytics pages
            - `utils/` — shared header, theme and helpers
            - `src/` — data processing and analytics logic
            - `data/` — supplied dataset
            - `reports/` and `notebooks/` — supporting analysis and outputs
            """
        )

st.warning(
    "Data limitation: the workbook alone does not establish dataset provenance. "
    "Treat findings as results from the supplied dataset, not verified official "
    "Sugar Cosmetics account performance.",
    icon="ℹ️",
)

st.divider()
st.caption(
    "Sugar Cosmetics Instagram Performance Analytics · Streamlit · "
    "Results are based on the selected supplied dataset."
)
