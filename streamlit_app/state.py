"""
Streamlit Session State & Persistence Management.
Manages user authentication, active examination pointers, and UI navigation state across reruns.
"""
from typing import Any, Optional
import streamlit as st
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal, init_db
from app.database.models import User


def get_db_session() -> Session:
    """Helper to yield an active database session for Streamlit operations."""
    return SessionLocal()


def init_session_state():
    """Initializes standard session keys with default values if not present."""
    # Ensure database tables exist
    init_db()

    defaults: dict[str, Any] = {
        "user": None,                  # Authenticated User dictionary
        "is_authenticated": False,     # Boolean login status
        "current_view": "Dashboard",   # Current active page view
        "active_exam_id": None,        # Examination currently in progress
        "current_question": None,      # Active NextQuestionResponse or dict
        "last_evaluation": None,       # Latest IBM Granite evaluation result
        "exam_complete": False,        # Flag signaling exam finish
        "submitting_answer": False,    # Guard against double submission
        "selected_doc_id": None,       # Selected document for examination or analysis
        "selected_report_exam_id": None,# Examination ID selected for report viewing
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def login_user(user: User):
    """Sets the authenticated user in session state."""
    st.session_state.user = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }
    st.session_state.is_authenticated = True
    st.session_state.current_view = "Dashboard"


def logout_user():
    """Clears user authentication and examination session state."""
    st.session_state.user = None
    st.session_state.is_authenticated = False
    st.session_state.active_exam_id = None
    st.session_state.current_question = None
    st.session_state.last_evaluation = None
    st.session_state.exam_complete = False
    st.session_state.current_view = "Sign In"


def get_current_user_id() -> Optional[int]:
    """Returns the authenticated user ID or None."""
    if st.session_state.get("is_authenticated") and st.session_state.get("user"):
        return st.session_state["user"].get("id")
    return None
