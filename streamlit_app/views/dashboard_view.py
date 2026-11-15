"""
Academic Dashboard View.
Presents overview metrics, in-progress examination resumption, recent documents, and examinations.
"""
import streamlit as st
from app.database.models import (
    Document,
    DocumentStatus,
    Examination,
    ExaminationReport,
    ExaminationStatus,
)
from streamlit_app.state import get_current_user_id, get_db_session


def render_dashboard_view():
    user = st.session_state.get("user")
    user_id = get_current_user_id()

    if not user_id:
        st.warning("Please sign in to view your dashboard.")
        return

    db = get_db_session()
    try:
        # Load user metrics
        doc_count = db.query(Document).filter(Document.user_id == user_id).count()
        exam_count = db.query(Examination).filter(Examination.user_id == user_id).count()
        report_count = db.query(ExaminationReport).filter(ExaminationReport.user_id == user_id).count()

        # Find any active in-progress exam
        active_exam = (
            db.query(Examination)
            .filter(
                Examination.user_id == user_id,
                Examination.status == ExaminationStatus.IN_PROGRESS,
            )
            .order_by(Examination.created_at.desc())
            .first()
        )

        # Recent Documents
        recent_docs = (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(5)
            .all()
        )

        # Recent Examinations
        recent_exams = (
            db.query(Examination)
            .filter(Examination.user_id == user_id)
            .order_by(Examination.created_at.desc())
            .limit(5)
            .all()
        )
    finally:
        db.close()

    # Welcome Banner
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <span class="badge badge-terracotta">Autonomous Multi-Agent Workspace</span>
            <h1 style="font-size: 32px; margin-top: 6px; margin-bottom: 4px;">Welcome, {user.get('name', 'Student')}</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Evidence-driven examination platform powered by Google Gemini and IBM Granite via watsonx.ai.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3 Metric Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Analyzed Documents</div>
                <div class="stat-value">{doc_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stat-card" style="border-left-color: var(--color-sage);">
                <div class="stat-label">Examinations Taken</div>
                <div class="stat-value">{exam_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="stat-card" style="border-left-color: var(--color-olive);">
                <div class="stat-label">Synthesized Reports</div>
                <div class="stat-value">{report_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # In-Progress Active Examination Resume Banner
    if active_exam:
        db = get_db_session()
        try:
            doc = db.query(Document).filter(Document.id == active_exam.document_id).first()
            doc_title = doc.original_filename if doc else f"Document #{active_exam.document_id}"
        finally:
            db.close()

        pct = round((active_exam.questions_asked_count / active_exam.max_questions) * 100) if active_exam.max_questions > 0 else 0

        st.markdown(
            f"""
            <div class="editorial-card" style="border-left: 5px solid var(--color-terracotta); background: #FCFAF7;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="badge badge-terracotta">Active In-Progress Examination</span>
                        <h3 style="margin-top: 6px; margin-bottom: 2px;">{doc_title}</h3>
                        <p style="color: var(--color-warmgray); font-size: 13px; margin: 0;">
                            Progress: {active_exam.questions_asked_count} of {active_exam.max_questions} questions answered ({pct}%)
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(pct / 100.0)

        col_res1, col_res2 = st.columns([1, 4])
        with col_res1:
            if st.button("Resume Examination", type="primary", use_container_width=True):
                st.session_state.active_exam_id = active_exam.id
                st.session_state.current_view = "Examination Room"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # Quick Navigation / Action Row
    st.markdown("### Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("📄 Upload Curriculum PDF", use_container_width=True):
            st.session_state.current_view = "Documents & Upload"
            st.rerun()
    with qa2:
        if st.button("⚔️ Start Examination", use_container_width=True):
            st.session_state.current_view = "Examinations"
            st.rerun()
    with qa3:
        if st.button("🧠 Knowledge Profile", use_container_width=True):
            st.session_state.current_view = "Knowledge Profile"
            st.rerun()
    with qa4:
        if st.button("📊 ML Learning Analytics", use_container_width=True):
            st.session_state.current_view = "ML Learning Analytics"
            st.rerun()

    st.markdown("---")

    # Tables: Recent Documents & Recent Examinations
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Recent Documents")
        if not recent_docs:
            st.info("No documents uploaded yet. Upload a syllabus or lecture module PDF to get started.")
        else:
            for doc in recent_docs:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #FFFFFF; border: 1px solid var(--color-sand); border-radius: 8px; margin-bottom: 8px;">
                            <div>
                                <div style="font-weight: 600; font-size: 14px;">{doc.original_filename}</div>
                                <div style="color: var(--color-warmgray); font-size: 12px;">{doc.page_count or 0} pages • {doc.word_count or 0} words</div>
                            </div>
                            <div>
                                <span class="badge badge-sand">{doc.status.value if hasattr(doc.status, 'value') else str(doc.status)}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with col_right:
        st.markdown("### Recent Examinations")
        if not recent_exams:
            st.info("No examinations conducted yet. Start your first autonomous oral examination.")
        else:
            for exam in recent_exams:
                status_str = exam.status.value if hasattr(exam.status, "value") else str(exam.status)
                badge_class = "badge-sage" if status_str == "COMPLETED" else "badge-terracotta" if status_str == "IN_PROGRESS" else "badge-sand"
                with st.container():
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #FFFFFF; border: 1px solid var(--color-sand); border-radius: 8px; margin-bottom: 8px;">
                            <div>
                                <div style="font-weight: 600; font-size: 14px;">Exam #{exam.id} (Doc #{exam.document_id})</div>
                                <div style="color: var(--color-warmgray); font-size: 12px;">Questions: {exam.questions_asked_count}/{exam.max_questions} • Difficulty: {exam.current_difficulty.value if hasattr(exam.current_difficulty, 'value') else str(exam.current_difficulty)}</div>
                            </div>
                            <div>
                                <span class="badge {badge_class}">{status_str}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
