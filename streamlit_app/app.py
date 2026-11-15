"""
ExamForge Streamlit Main Application.
Autonomous AI Academic Examination Platform powered by Google Gemini, IBM Granite,
LangGraph, ChromaDB, PostgreSQL, and Scikit-learn.
"""
import os
import sys
from pathlib import Path

# Ensure backend modules are directly importable from workspace root
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from streamlit_app.state import init_session_state, logout_user
from streamlit_app.styles import apply_styles
from streamlit_app.views.auth_view import render_auth_view
from streamlit_app.views.dashboard_view import render_dashboard_view
from streamlit_app.views.documents_view import render_documents_view
from streamlit_app.views.examination_view import render_examination_view
from streamlit_app.views.knowledge_view import render_knowledge_view
from streamlit_app.views.ml_analytics_view import render_ml_analytics_view
from streamlit_app.views.question_bank_view import render_question_bank_view
from streamlit_app.views.reports_view import render_reports_view
from streamlit_app.views.settings_view import render_settings_view

# ── SIDEBAR NAVIGATION DEFINITION ─────────────────────────────────────────────
# Each entry: (icon, label, section_group)
NAV_ITEMS = [
    ("📊", "Dashboard",            "overview"),
    ("📄", "Documents & Upload",   "overview"),
    ("📝", "Question Bank",        "study"),
    ("🎯", "Examinations",         "study"),
    ("📈", "Examination Reports",  "analysis"),
    ("🧠", "Knowledge Profile",    "analysis"),
    ("⚡", "ML Learning Analytics", "analysis"),
    ("⚙️", "Settings & Status",    "system"),
]


def _render_sidebar_nav(current_view: str):
    """Renders the modern styled sidebar navigation with icons and grouping."""
    section_labels = {
        "overview": "OVERVIEW",
        "study": "STUDY",
        "analysis": "ANALYSIS",
        "system": "SYSTEM",
    }
    prev_group = None
    for icon, label, group in NAV_ITEMS:
        # Section divider with label when a new group begins
        if group != prev_group:
            margin = "20px" if prev_group is not None else "8px"
            st.markdown(
                f'<div class="nav-section-label" style="margin-top:{margin};">'
                f'{section_labels[group]}</div>',
                unsafe_allow_html=True,
            )
            prev_group = group

        is_active = (label == current_view)
        active_cls = " nav-item-active" if is_active else ""
        key = f"nav_{label}"

        # Render clickable navigation item via a Streamlit button styled as a nav row
        if st.button(
            f"{icon}  {label}",
            key=key,
            use_container_width=True,
            type="secondary",
        ):
            if label != current_view:
                st.session_state.current_view = label
                st.rerun()

        # Inject an active-state marker right after the active button so CSS can target it
        if is_active:
            st.markdown(
                '<div class="nav-active-marker" style="display:none;"></div>',
                unsafe_allow_html=True,
            )


def main():
    st.set_page_config(
        page_title="ExamForge — Autonomous AI Examination Platform",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply editorial theme styles
    apply_styles()

    # Initialize persistent session state & database tables
    init_session_state()

    is_auth = st.session_state.get("is_authenticated", False)
    user = st.session_state.get("user")

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand header
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-name">ExamForge</div>
                <div class="sidebar-brand-tagline">Autonomous Academic Examiner</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_auth and user:
            # User card
            st.markdown(
                f"""
                <div class="sidebar-user-card">
                    <div class="sidebar-user-avatar">{user.get('name', 'S')[0].upper()}</div>
                    <div class="sidebar-user-info">
                        <div class="sidebar-user-name">{user.get('name', 'Student')}</div>
                        <div class="sidebar-user-email">{user.get('email', '')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Reconcile navigation state
            current = st.session_state.get("current_view", "Dashboard")
            valid_labels = [item[1] for item in NAV_ITEMS]
            if current not in valid_labels:
                current = "Dashboard"
                st.session_state.current_view = current

            # Render styled navigation
            _render_sidebar_nav(current)

            # Sign-out button at the bottom
            st.markdown('<div class="sidebar-signout-spacer"></div>', unsafe_allow_html=True)
            if st.button("↩  Sign Out", key="btn_signout", use_container_width=True):
                logout_user()
                st.rerun()

        else:
            st.markdown(
                """
                <div style="padding: 16px 0;">
                    <p style="font-size: 13px; color: var(--color-warmgray); line-height: 1.5;">
                        ExamForge conducts autonomous oral examinations using Google Gemini, evaluates reasoning with IBM Granite, and analyzes performance with Scikit-learn.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── MAIN CONTENT VIEW ROUTING ─────────────────────────────────────────────
    if not is_auth:
        render_auth_view()
    else:
        view = st.session_state.get("current_view", "Dashboard")

        if view == "Dashboard":
            render_dashboard_view()
        elif view == "Documents & Upload":
            render_documents_view()
        elif view == "Question Bank":
            render_question_bank_view()
        elif view == "Examinations" or view == "Examination Room":
            render_examination_view()
        elif view == "Examination Reports":
            render_reports_view()
        elif view == "Knowledge Profile":
            render_knowledge_view()
        elif view == "ML Learning Analytics":
            render_ml_analytics_view()
        elif view == "Settings & Status":
            render_settings_view()
        else:
            render_dashboard_view()


if __name__ == "__main__":
    main()
