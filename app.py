"""
app.py — Entry point for the Tuition Management System.
Run with:  streamlit run app.py
"""
import sys
import os

# ── Ensure project root is on sys.path so sub-packages resolve cleanly ─────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from database.db import init_db

# ── Page config (must be first Streamlit call) ──────────────────────────────────
st.set_page_config(
    page_title="Tuition Manager",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise DB once per process ─────────────────────────────────────────────
@st.cache_resource
def initialise_database():
    init_db()

initialise_database()

# ── Custom CSS ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar nav */
    [data-testid="stSidebarNav"] { display: none; }

    /* Global font */
    html, body, [class*="css"]  { font-family: 'Inter', 'Segoe UI', sans-serif; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="metric-container"] > div { color: #3730A3; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; font-weight: 600; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #6366F1 !important; color: #3730A3; }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1, #3730A3);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4F46E5, #312E81);
    }

    /* Dataframe */
    [data-testid="stDataFrameContainer"] { border-radius: 8px; overflow: hidden; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #1E1B4B; }
    [data-testid="stSidebar"] * { color: #E0E7FF !important; }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        border-radius: 8px;
        font-size: 0.95rem;
        padding: 10px 14px;
        margin-bottom: 4px;
        color: #C7D2FE !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(99,102,241,0.2) !important;
        color: white !important;
    }
    .nav-active > button {
        background: rgba(99,102,241,0.35) !important;
        color: white !important;
        border-left: 3px solid #818CF8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state defaults ──────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ── Sidebar navigation ──────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("📊", "Dashboard"),
    ("👨‍🎓", "Students"),
    ("📅", "Schedules"),
    ("📖", "Sessions"),
    ("📝", "Tests"),
    ("📄", "Reports"),
]

with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center;padding:18px 0 6px 0;'>
            <div style='font-size:2.2rem;'>📚</div>
            <div style='font-size:1.15rem;font-weight:700;color:#E0E7FF;
                        letter-spacing:0.5px;'>Tuition Manager</div>
            <div style='font-size:0.78rem;color:#818CF8;margin-top:2px;'>
                Private Classes Assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:#312E81;margin:10px 0 16px 0'>", unsafe_allow_html=True)

    for icon, page_name in NAV_ITEMS:
        is_active = st.session_state.page == page_name
        container = st.container()
        # Wrap in a div to allow active-state CSS targeting
        if is_active:
            with container:
                st.markdown('<div class="nav-active">', unsafe_allow_html=True)
                if st.button(f"  {icon}  {page_name}", key=f"nav_{page_name}"):
                    st.session_state.page = page_name
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with container:
                if st.button(f"  {icon}  {page_name}", key=f"nav_{page_name}"):
                    st.session_state.page = page_name
                    st.rerun()

    st.markdown("<hr style='border-color:#312E81;margin:16px 0 10px 0'>", unsafe_allow_html=True)

    # Quick stats in sidebar
    from services.student_service import get_student_count
    import datetime
    student_count = get_student_count()
    today = datetime.date.today()
    from services.session_service import get_sessions_for_date
    todays_count = len(get_sessions_for_date(today))

    st.markdown(
        f"""
        <div style='background:rgba(99,102,241,0.15);border-radius:8px;
                    padding:12px 14px;margin-top:8px;'>
            <div style='font-size:0.78rem;color:#A5B4FC;margin-bottom:6px;
                        text-transform:uppercase;letter-spacing:1px;'>Quick Stats</div>
            <div style='font-size:0.88rem;color:#E0E7FF;'>👨‍🎓 {student_count} active students</div>
            <div style='font-size:0.88rem;color:#E0E7FF;margin-top:4px;'>
                📅 {todays_count} class{'es' if todays_count != 1 else ''} today</div>
            <div style='font-size:0.75rem;color:#818CF8;margin-top:6px;'>
                {today.strftime('%d %B %Y')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Route to page ──────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "Dashboard":
    from ui.dashboard import render
    render()
elif page == "Students":
    from ui.students_page import render
    render()
elif page == "Schedules":
    from ui.schedule_page import render
    render()
elif page == "Sessions":
    from ui.sessions_page import render
    render()
elif page == "Tests":
    from ui.tests_page import render
    render()
elif page == "Reports":
    from ui.reports_page import render
    render()
