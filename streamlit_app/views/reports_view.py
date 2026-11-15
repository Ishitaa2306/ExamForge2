"""
Examination Reports & PDF Export View.
Synthesizes overall performance, topic strengths, conceptual gaps, and prioritized study roadmaps.
"""
import streamlit as st

from app.database.models import (
    Document,
    DocumentTopic,
    Examination,
    ExaminationReport,
    User,
)
from app.services.report_service import ReportService
from streamlit_app.state import get_current_user_id, get_db_session


def render_reports_view():
    user_id = get_current_user_id()
    if not user_id:
        st.warning("Please sign in to view examination reports.")
        return

    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">Agent 4: Report Synthesis (Gemini)</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Academic Performance Reports</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Comprehensive academic reports synthesized by Google Gemini from IBM Granite evaluation evidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db = get_db_session()
    try:
        reports = (
            db.query(ExaminationReport)
            .filter(ExaminationReport.user_id == user_id)
            .order_by(ExaminationReport.generated_at.desc())
            .all()
        )
    finally:
        db.close()

    if not reports:
        st.info("No examination reports generated yet. Complete an examination to generate your report.")
        return

    # Report selection dropdown
    report_options = {}
    db = get_db_session()
    try:
        for r in reports:
            doc = db.query(Document).filter(Document.id == r.document_id).first()
            doc_name = doc.original_filename if doc else f"Doc #{r.document_id}"
            score_pct = round((r.overall_score or 0) * 100)
            report_options[r.examination_id] = f"Exam #{r.examination_id} — {doc_name} (Score: {score_pct}%) — {r.generated_at.strftime('%Y-%m-%d %H:%M') if r.generated_at else ''}"
    finally:
        db.close()

    default_exam_id = st.session_state.get("selected_report_exam_id")
    if default_exam_id not in report_options:
        default_exam_id = list(report_options.keys())[0]

    selected_exam_id = st.selectbox(
        "Select Examination Report",
        options=list(report_options.keys()),
        format_func=lambda x: report_options[x],
        index=list(report_options.keys()).index(default_exam_id) if default_exam_id in report_options else 0,
    )

    db = get_db_session()
    try:
        report = (
            db.query(ExaminationReport)
            .filter(ExaminationReport.examination_id == selected_exam_id)
            .first()
        )
        exam = (
            db.query(Examination)
            .filter(Examination.id == selected_exam_id)
            .first()
        )
        doc = db.query(Document).filter(Document.id == report.document_id).first()
        user_record = db.query(User).filter(User.id == user_id).first()

        if not report or not exam:
            st.error("Report details not found.")
            return

        overall_score = round((report.overall_score or 0.0) * 100, 1)

        # Overview Banner & Download Button
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown(
                f"""
                <div class="editorial-card" style="border-left: 5px solid var(--color-terracotta);">
                    <span class="badge badge-sage">Verified Academic Assessment</span>
                    <h2 style="font-size: 26px; margin: 6px 0;">{doc.original_filename if doc else 'Curriculum'}</h2>
                    <p style="color: var(--color-warmgray); font-size: 13px; margin: 0;">
                        Examinee: <strong>{user_record.name}</strong> • Completed: {report.generated_at.strftime('%B %d, %Y')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_head2:
            # Generate PDF using ReportLab
            try:
                pdf_bytes = ReportService.generate_pdf(
                    db=db,
                    report=report,
                    examination=exam,
                    user=user_record,
                )
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"ExamForge-Report-{exam.id}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as pdf_err:
                st.caption(f"PDF generation note: {pdf_err}")

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Mastery", f"{overall_score}%")
        m2.metric("Questions Examined", f"{exam.questions_asked_count}")
        m3.metric("Strong Concepts", f"{len(report.strong_concepts or [])}")
        m4.metric("Identified Gaps", f"{len(report.weak_concepts or [])}")

        st.progress(overall_score / 100.0)

        # Topic Breakdown
        st.markdown("### Topic-Wise Mastery")
        if report.topic_scores and isinstance(report.topic_scores, dict):
            topics = db.query(DocumentTopic).filter(DocumentTopic.document_id == report.document_id).all()
            topic_name_map = {str(t.id): t.name for t in topics}

            t_cols = st.columns(min(len(report.topic_scores), 3)) if report.topic_scores else [st]
            for idx, (t_id, score_val) in enumerate(report.topic_scores.items()):
                t_name = topic_name_map.get(str(t_id), f"Topic #{t_id}")
                pct_val = round(float(score_val) * 100)
                badge_type = "badge-sage" if pct_val >= 70 else "badge-terracotta" if pct_val < 50 else "badge-olive"

                col_idx = idx % min(len(report.topic_scores), 3)
                with t_cols[col_idx]:
                    st.markdown(
                        f"""
                        <div class="stat-card" style="margin-bottom: 12px; border-left-color: {'#788875' if pct_val >= 70 else '#B8755D'};">
                            <span class="badge {badge_type}">{pct_val}% Mastery</span>
                            <div style="font-weight: 600; font-size: 14px; margin-top: 6px;">{t_name}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # Conceptual Mastery Breakdown
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("### Verified Strong Concepts")
            if not report.strong_concepts:
                st.info("No strong concepts recorded yet.")
            else:
                for c in report.strong_concepts:
                    st.markdown(f"✅ **{c}**")

            if report.partial_concepts:
                st.markdown("### Partially Understood Concepts")
                for c in report.partial_concepts:
                    st.markdown(f"⚠️ **{c}**")

        with c_right:
            st.markdown("### Priority Knowledge Gaps")
            if not report.weak_concepts:
                st.success("No critical knowledge gaps detected.")
            else:
                for c in report.weak_concepts:
                    st.markdown(f"❌ **{c}**")

        # Study Recommendations
        st.markdown("### Prioritized Study Roadmap")
        if not report.recommendations:
            st.info("Continue standard revision across all curriculum topics.")
        else:
            for rec in report.recommendations:
                st.markdown(f"💡 {rec}")

    finally:
        db.close()
