
"""Premium Sugar Cosmetics theme for all Streamlit pages and Plotly charts."""

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

SUGAR_PINK = "#E85D87"
SUGAR_PLUM = "#8E476B"
SUGAR_DARK = "#1C131B"
SUGAR_PALE = "#211720"
SUGAR_SURFACE = "#2B202A"
SUGAR_BORDER = "#493542"
SUGAR_INK = "#F9F2F6"
SUGAR_MUTED = "#BDAEB9"
SUGAR_INPUT = "#191219"
SUGAR_CHART = "#261C25"
SUGAR_GRID = "#493542"
SUGAR_ROSE = "#DDA0B8"


def apply_theme() -> None:
    """Apply the same premium dark-plum visual system throughout the app."""

    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            --sugar-pink: #E85D87;
            --sugar-plum: #8E476B;
            --sugar-bg: #211720;
            --sugar-card: #2B202A;
            --sugar-border: #493542;
            --sugar-text: #F9F2F6;
            --sugar-muted: #BDAEB9;
            --sugar-input: #191219;
        }

        /* Main application and every Streamlit content wrapper */
        html, body, #root, .stApp,
        [data-testid="stApp"],
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > section,
        [data-testid="stMain"],
        section[data-testid="stMain"],
        [data-testid="stMain"] > div,
        [data-testid="stMainBlockContainer"],
        .main, .main .block-container,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
            background: var(--sugar-bg) !important;
            color: var(--sugar-text) !important;
        }

        [data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 1600px !important;
            padding-top: 1.8rem !important;
            padding-bottom: 3rem !important;
            background: var(--sugar-bg) !important;
        }

        /* Main content typography */
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4 {
            color: var(--sugar-text) !important;
            letter-spacing: -0.025em;
            font-weight: 720 !important;
        }

        [data-testid="stMain"] p,
        [data-testid="stMain"] li,
        [data-testid="stMain"] label,
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
            color: var(--sugar-text) !important;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {
            color: var(--sugar-muted) !important;
        }

        /* Sidebar: deep plum, subtle border, consistent typography */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebar"] > div:first-child {
            background: var(--sugar-bg) !important;
            color: var(--sugar-text) !important;
            border-right: 1px solid var(--sugar-border) !important;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: var(--sugar-text);
        }

        /* Navigation links styled as compact, clickable app buttons */
        [data-testid="stSidebarNav"] {
            padding: 0.25rem 0.4rem 0.45rem 0.4rem !important;
        }
        [data-testid="stSidebarNav"] a {
            box-sizing: border-box !important;
            min-height: 34px !important;
            margin: 2px 0 !important;
            padding: 0.38rem 0.68rem !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            background: rgba(255,255,255,0.018) !important;
            transition: background 140ms ease, border-color 140ms ease, transform 140ms ease;
        }
        [data-testid="stSidebarNav"] a p {
            font-weight: 620 !important;
            font-size: 0.86rem !important;
            line-height: 1.15 !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: linear-gradient(110deg, rgba(232,93,135,0.18), rgba(142,71,107,0.16)) !important;
            border-color: rgba(232,93,135,0.38) !important;
            transform: translateX(2px);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(110deg, rgba(232,93,135,0.24), rgba(142,71,107,0.20)) !important;
            border: 1px solid rgba(232,93,135,0.62) !important;
            box-shadow: inset 3px 0 0 #E85D87, 0 4px 12px rgba(0,0,0,0.10) !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] p {
            color: #FFF7FA !important;
            font-weight: 760 !important;
        }

        /* Dynamic page summary rendered beneath the navigation */
        .sugar-sidebar-info {
            margin: 0.7rem 0.55rem 0.8rem 0.55rem;
            padding: 1rem 0.9rem 0.85rem 0.9rem;
            border: 1px solid #5A3A50;
            border-radius: 13px;
            background: linear-gradient(155deg, #30212D 0%, #241923 100%);
            box-shadow: 0 7px 18px rgba(0,0,0,0.12);
        }
        .sugar-sidebar-eyebrow {
            color: #F58DB0; font-size: 0.61rem; font-weight: 800;
            letter-spacing: 0.13em; margin-bottom: 0.5rem;
        }
        .sugar-sidebar-title {
            color: #FFF7FA; font-size: 1rem; font-weight: 760;
            line-height: 1.3; margin-bottom: 0.42rem;
        }
        .sugar-sidebar-description {
            color: #D4C2CE; font-size: 0.78rem; line-height: 1.48;
        }
        .sugar-sidebar-divider {
            height: 1px; background: #513447; margin: 0.85rem 0 0.65rem 0;
        }
        .sugar-sidebar-stat {
            display: flex; flex-direction: column; gap: 0.15rem;
            padding: 0.35rem 0; overflow-wrap: anywhere;
        }
        .sugar-sidebar-stat span { color: #BDAEB9; font-size: 0.68rem; }
        .sugar-sidebar-stat strong { color: #FFF7FA; font-size: 0.8rem; font-weight: 700; }
        .sugar-sidebar-foot {
            color: #A997A5; font-size: 0.64rem; line-height: 1.4; margin-top: 0.55rem;
        }

        [data-testid="stSidebar"] [aria-current="page"] {
            background: var(--sugar-surface) !important;
            border-radius: 8px !important;
        }

        /* Cards and bordered containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--sugar-surface) !important;
            border: 1px solid var(--sugar-border) !important;
            border-radius: 14px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div {
            background: transparent !important;
        }

        [data-testid="stHorizontalBlock"],
        [data-testid="stColumn"],
        [data-testid="stVerticalBlock"] {
            background: transparent;
        }

        /* KPI cards */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #342632, #2B202A) !important;
            border: 1px solid var(--sugar-border) !important;
            border-top: 2px solid var(--sugar-plum) !important;
            border-radius: 12px !important;
            padding: 16px 17px !important;
            min-height: 105px;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            color: var(--sugar-muted) !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: var(--sugar-text) !important;
            font-weight: 720 !important;
        }

        [data-testid="stMetricDelta"] {
            color: var(--sugar-rose) !important;
        }

        /* Expanders */
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] details > div,
        [data-testid="stExpander"] summary {
            background: var(--sugar-surface) !important;
            border-color: var(--sugar-border) !important;
            border-radius: 10px !important;
        }

        /* Input fields and dropdowns */
        [data-testid="stMain"] input,
        [data-testid="stMain"] textarea,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] {
            background: var(--sugar-input) !important;
            color: var(--sugar-text) !important;
            border-color: var(--sugar-border) !important;
            border-radius: 8px !important;
        }

        [data-baseweb="select"] *,
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"],
        [role="option"] {
            background-color: var(--sugar-input) !important;
            color: var(--sugar-text) !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: var(--sugar-muted) !important;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] button {
            background: var(--sugar-plum) !important;
            color: #FFFFFF !important;
            border: 1px solid #A76588 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: background 150ms ease, border-color 150ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            background: var(--sugar-pink) !important;
            border-color: var(--sugar-pink) !important;
            color: #FFFFFF !important;
        }

        /* Data tables */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stDataEditor"] {
            background: var(--sugar-surface) !important;
            border: 1px solid var(--sugar-border) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            background: #302330 !important;
            border: 1px solid var(--sugar-border) !important;
            border-radius: 10px !important;
        }

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] div {
            color: var(--sugar-text) !important;
        }

        /* Links, dividers and interactive accents */
        a {
            color: var(--sugar-rose) !important;
        }

        hr {
            border-color: var(--sugar-border) !important;
        }

        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label,
        [data-testid="stToggle"] label {
            color: var(--sugar-text) !important;
        }

        /* Hide excess top chrome without hiding Streamlit controls */
        [data-testid="stHeader"] {
            background: var(--sugar-bg) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Shared Plotly chart theme
    template = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=SUGAR_PALE,
            plot_bgcolor=SUGAR_CHART,
            font=dict(
                family="Arial, sans-serif",
                color=SUGAR_INK,
                size=12,
            ),
            title=dict(
                font=dict(color=SUGAR_INK, size=16),
                x=0.01,
                xanchor="left",
            ),
            colorway=[
                SUGAR_PINK,
                SUGAR_ROSE,
                "#B77A9A",
                "#F4E9EF",
                SUGAR_PLUM,
                "#A88C9D",
            ],
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                linecolor=SUGAR_BORDER,
                tickfont=dict(color=SUGAR_MUTED),
                title_font=dict(color=SUGAR_TEXT if False else SUGAR_INK),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=SUGAR_GRID,
                zeroline=False,
                linecolor=SUGAR_BORDER,
                tickfont=dict(color=SUGAR_MUTED),
                title_font=dict(color=SUGAR_INK),
            ),
            legend=dict(
                font=dict(color=SUGAR_INK),
                bgcolor="rgba(43,32,42,0.92)",
            ),
            margin=dict(l=12, r=12, t=52, b=12),
            hoverlabel=dict(
                bgcolor=SUGAR_DARK,
                bordercolor=SUGAR_PINK,
                font=dict(color="#FFFFFF"),
            ),
        )
    )

    pio.templates["sugar"] = template
    px.defaults.template = "sugar"
