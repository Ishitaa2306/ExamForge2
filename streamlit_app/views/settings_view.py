"""
Settings & AI Infrastructure Verification View.
Monitors system health, database connectivity, and provides live verification probes
for Google Gemini and IBM Granite via watsonx.ai without exposing secrets.
"""
import streamlit as st
from sqlalchemy import text

from app.core.config import settings
from app.llm.model_router import AGENT_MODEL_MAPPING, get_gemini_client, get_granite_client
from streamlit_app.state import get_current_user_id, get_db_session


def render_settings_view():
    user = st.session_state.get("user")
    user_id = get_current_user_id()

    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">System Infrastructure</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Settings & AI Verification</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Inspect database connectivity, examinee profile, and execute live health verification probes against Google Gemini and IBM Granite.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_profile, tab_providers, tab_mapping = st.tabs([
        "Examinee Profile",
        "AI Providers & Database",
        "Six-Agent Architecture",
    ])

    # ── TAB 1: PROFILE ────────────────────────────────────────────────────────
    with tab_profile:
        st.markdown("### Registered Examinee")
        if user:
            st.markdown(
                f"""
                <div class="editorial-card">
                    <div style="font-size: 18px; font-weight: 700;">{user.get('name', 'Student')}</div>
                    <div style="color: var(--color-warmgray); font-size: 14px; margin-top: 2px;">{user.get('email', '')}</div>
                    <div style="margin-top: 12px;">
                        <span class="badge badge-sage">Active Examinee Session</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Not signed in.")

    # ── TAB 2: PROVIDERS & DB ─────────────────────────────────────────────────
    with tab_providers:
        st.markdown("### Relational Database Status")
        db = get_db_session()
        db_connected = False
        db_error = ""
        try:
            db.execute(text("SELECT 1"))
            db_connected = True
        except Exception as exc:
            db_connected = False
            db_error = str(exc)
        finally:
            db.close()

        engine_type = settings.DATABASE_URL.split("://")[0] if "://" in settings.DATABASE_URL else "unknown"
        if db_connected:
            st.success(f"Database: **Connected** (Engine: `{engine_type.upper()}`)")
        else:
            st.error(f"Database: **Disconnected** — {db_error}")

        st.markdown("---")

        st.markdown("### Real AI Provider Connectivity")
        st.caption("Perform live inference pings against the AI backends to ensure credentials and models are functional.")

        col_gem, col_gran = st.columns(2)

        # Google Gemini Card
        with col_gem:
            gemini_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
            badge = "badge-sage" if gemini_configured else "badge-terracotta"
            st.markdown(
                f"""
                <div class="editorial-card" style="border-left: 4px solid var(--color-terracotta);">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="badge {badge}">{'Configured' if gemini_configured else 'Unconfigured'}</span>
                        <span class="badge badge-sand">Google Gemini</span>
                    </div>
                    <h4 style="margin: 8px 0 4px 0;">Google Generative AI</h4>
                    <p style="color: var(--color-warmgray); font-size: 12px; margin: 0;">
                        Model: <code>{settings.GEMINI_MODEL_ID or 'Not Set'}</code><br>
                        API Key: {'••••' + settings.GEMINI_API_KEY[-4:] if gemini_configured and len(settings.GEMINI_API_KEY) > 4 else 'Not Set'}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Verify Gemini Connectivity", key="test_gemini"):
                if not gemini_configured:
                    st.error("GEMINI_API_KEY is not configured in .env.")
                else:
                    with st.spinner("Pinging Google Gemini API..."):
                        try:
                            client = get_gemini_client()
                            res = client.test_connection()
                            if res.get("status") == "connected":
                                st.success(f"Gemini Connected! Latency: {res.get('latency_ms', 0):.1f}ms")
                            else:
                                st.error(f"Gemini Error: {res.get('message')}")
                        except Exception as e:
                            st.error(f"Gemini connection failed: {e}")

        # IBM Granite Card
        with col_gran:
            granite_configured = bool(
                settings.WATSONX_API_KEY
                and settings.WATSONX_API_KEY.strip()
                and settings.WATSONX_PROJECT_ID
                and settings.WATSONX_PROJECT_ID.strip()
            )
            badge_gran = "badge-sage" if granite_configured else "badge-terracotta"
            st.markdown(
                f"""
                <div class="editorial-card" style="border-left: 4px solid var(--color-sage);">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="badge {badge_gran}">{'Configured' if granite_configured else 'Unconfigured'}</span>
                        <span class="badge badge-sand">IBM Granite</span>
                    </div>
                    <h4 style="margin: 8px 0 4px 0;">IBM watsonx.ai</h4>
                    <p style="color: var(--color-warmgray); font-size: 12px; margin: 0;">
                        Model: <code>{settings.GRANITE_MODEL_ID or 'Not Set'}</code><br>
                        URL: <code>{settings.WATSONX_URL}</code><br>
                        Project ID: {'••••' + settings.WATSONX_PROJECT_ID[-4:] if granite_configured and len(settings.WATSONX_PROJECT_ID) > 4 else 'Not Set'}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Verify IBM Granite Connectivity", key="test_granite"):
                if not granite_configured:
                    st.error("WATSONX_API_KEY or WATSONX_PROJECT_ID is not configured in .env.")
                else:
                    with st.spinner("Pinging IBM watsonx.ai Granite..."):
                        try:
                            client = get_granite_client()
                            res = client.test_connection()
                            if res.get("status") == "connected":
                                st.success(f"Granite Connected! Latency: {res.get('latency_ms', 0):.1f}ms")
                            else:
                                st.error(f"Granite Error: {res.get('message')}")
                        except Exception as e:
                            st.error(f"Granite connection failed: {e}")

    # ── TAB 3: SIX AGENT MAPPING ──────────────────────────────────────────────
    with tab_mapping:
        st.markdown("### Six-Agent Responsibility Allocation")
        st.caption("ExamForge maintains strict model routing across its six dedicated AI roles.")

        mapping_data = [
            {"Agent": "Agent 1: Document Understanding", "Provider": "Google Gemini", "Model": settings.GEMINI_MODEL_ID, "Responsibility": "Extracts hierarchical syllabus modules, formulas, definitions, and chunks into ChromaDB."},
            {"Agent": "Agent 2: Question Generation", "Provider": "Google Gemini", "Model": settings.GEMINI_MODEL_ID, "Responsibility": "Authors grounded questions across 8 cognitive categories with authoritative rubrics."},
            {"Agent": "Agent 3: Autonomous Examiner", "Provider": "Google Gemini", "Model": settings.GEMINI_MODEL_ID, "Responsibility": "Conducts oral examinations, analyzes evaluation evidence, and formulates adaptive follow-ups."},
            {"Agent": "Agent 4: Final Report Synthesis", "Provider": "Google Gemini", "Model": settings.GEMINI_MODEL_ID, "Responsibility": "Synthesizes overall academic performance reports and prioritized study roadmaps."},
            {"Agent": "Agent 5: Answer Evaluation", "Provider": "IBM Granite (watsonx.ai)", "Model": settings.GRANITE_MODEL_ID, "Responsibility": "Semantically scores student answers across 5 weighted academic criteria."},
            {"Agent": "Agent 6: Knowledge Assessment", "Provider": "IBM Granite (watsonx.ai)", "Model": settings.GRANITE_MODEL_ID, "Responsibility": "Assesses cumulative topic mastery (Strong, Partial, Weak) from real evidence."},
        ]
        st.dataframe(mapping_data, use_container_width=True)
