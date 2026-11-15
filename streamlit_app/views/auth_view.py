"""
Sign-In and Registration View.
"""
import streamlit as st
from app.core.security import hash_password, verify_password
from app.database.models import User
from streamlit_app.state import get_db_session, login_user


def render_auth_view():
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-size: 36px; margin-bottom: 8px;">ExamForge</h1>
            <p style="color: var(--color-warmgray); font-size: 15px;">
                Autonomous Evidence-Driven Academic Examination Platform
            </p>
            <div style="display: inline-flex; gap: 8px; margin-top: 10px;">
                <span class="badge badge-terracotta">Google Gemini</span>
                <span class="badge badge-sage">IBM Granite</span>
                <span class="badge badge-sand">LangGraph</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.markdown("### Welcome Back")
            st.caption("Sign in with your registered examinee credentials.")

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="student@example.edu")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please provide both email and password.")
                    else:
                        db = get_db_session()
                        try:
                            user = db.query(User).filter(User.email == email.strip().lower()).first()
                            if not user or not verify_password(password, user.hashed_password):
                                st.error("Incorrect email address or password.")
                            else:
                                login_user(user)
                                st.success(f"Welcome back, {user.name}!")
                                st.rerun()
                        finally:
                            db.close()

        with tab_register:
            st.markdown("### Register Examinee")
            st.caption("Create an account to track your academic examinations.")

            with st.form("register_form", clear_on_submit=False):
                name = st.text_input("Full Name", placeholder="e.g. Jane Doe")
                reg_email = st.text_input("Email Address", placeholder="jane@example.edu")
                reg_password = st.text_input("Password (min. 6 characters)", type="password", placeholder="••••••••")
                reg_password_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                reg_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                if reg_submitted:
                    if not name or not reg_email or not reg_password:
                        st.error("Please fill in all required fields.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif reg_password != reg_password_confirm:
                        st.error("Passwords do not match.")
                    else:
                        db = get_db_session()
                        try:
                            existing = db.query(User).filter(User.email == reg_email.strip().lower()).first()
                            if existing:
                                st.error("An account with this email address is already registered.")
                            else:
                                new_user = User(
                                    email=reg_email.strip().lower(),
                                    name=name.strip(),
                                    hashed_password=hash_password(reg_password),
                                )
                                db.add(new_user)
                                db.commit()
                                db.refresh(new_user)
                                login_user(new_user)
                                st.success("Account created successfully! Welcome to ExamForge.")
                                st.rerun()
                        finally:
                            db.close()
