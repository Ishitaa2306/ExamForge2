"""
Examination View — Start, Resume, Active Examination Room & Adaptive Probing.
Orchestrated by LangGraph, evaluated by IBM Granite via watsonx.ai, and adapted by Google Gemini.
"""
import time
import streamlit as st

from app.database.models import (
    AnswerEvaluation,
    Document,
    DocumentStatus,
    Examination,
    ExaminationReport,
    ExaminationStatus,
    QuestionAsked,
    StudentAnswer,
)
from app.schemas.examinations import SubmitAnswerRequest
from app.services.examination_service import ExaminationService
from streamlit_app.state import get_current_user_id, get_db_session


def render_examination_view():
    user_id = get_current_user_id()
    if not user_id:
        st.warning("Please sign in to take examinations.")
        return

    # Check if we are currently in an active examination room
    active_exam_id = st.session_state.get("active_exam_id")

    if active_exam_id:
        _render_active_exam_session(active_exam_id, user_id)
    else:
        _render_exam_lobby(user_id)


def _render_exam_lobby(user_id: int):
    """Lobby for creating new examinations or resuming existing ones."""
    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">Agent 3: Autonomous Examiner (Gemini)</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Examination Room</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Conduct rigorous oral examinations grounded in syllabus documents. Answers are evaluated by IBM Granite and adaptive probes are formulated by Google Gemini.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_start, tab_resume, tab_history = st.tabs(["Start New Examination", "Resume In-Progress", "Examination History"])

    # ── TAB 1: START NEW ──────────────────────────────────────────────────────
    with tab_start:
        st.markdown("### Configure Examination Session")
        db = get_db_session()
        try:
            docs = (
                db.query(Document)
                .filter(Document.user_id == user_id, Document.status == DocumentStatus.ANALYZED)
                .all()
            )
            doc_options = {d.id: d.original_filename for d in docs}
        finally:
            db.close()

        if not doc_options:
            st.info("No analyzed documents available. Please upload a PDF curriculum module first.")
        else:
            with st.form("new_exam_form"):
                selected_doc = st.selectbox(
                    "Select Target Curriculum",
                    options=list(doc_options.keys()),
                    format_func=lambda x: doc_options[x],
                )
                max_q = st.slider(
                    "Number of Examination Questions",
                    min_value=5,
                    max_value=30,
                    value=15,
                    step=5,
                    help="Gemini adapts question difficulty dynamically as you progress.",
                )
                submit_start = st.form_submit_button("Enter Examination Room", type="primary")

                if submit_start:
                    db = get_db_session()
                    try:
                        exam = ExaminationService.create_examination(
                            db=db,
                            user_id=user_id,
                            document_id=selected_doc,
                            max_questions=max_q,
                        )
                        st.session_state.active_exam_id = exam.id
                        st.session_state.current_question = None
                        st.session_state.last_evaluation = None
                        st.session_state.exam_complete = False
                        st.session_state.current_view = "Examination Room"
                        st.rerun()
                    finally:
                        db.close()

    # ── TAB 2: RESUME ─────────────────────────────────────────────────────────
    with tab_resume:
        st.markdown("### In-Progress Sessions")
        db = get_db_session()
        try:
            in_progress = (
                db.query(Examination)
                .filter(
                    Examination.user_id == user_id,
                    Examination.status == ExaminationStatus.IN_PROGRESS,
                )
                .order_by(Examination.created_at.desc())
                .all()
            )

            if not in_progress:
                st.info("No examinations are currently paused or in-progress.")
            else:
                for exam in in_progress:
                    doc = db.query(Document).filter(Document.id == exam.document_id).first()
                    doc_title = doc.original_filename if doc else f"Document #{exam.document_id}"
                    pct = round((exam.questions_asked_count / exam.max_questions) * 100) if exam.max_questions > 0 else 0

                    with st.container():
                        st.markdown(
                            f"""
                            <div class="editorial-card" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 600; font-size: 15px;">{doc_title} (Exam #{exam.id})</div>
                                        <div style="color: var(--color-warmgray); font-size: 12px; margin-top: 2px;">
                                            Progress: {exam.questions_asked_count} of {exam.max_questions} questions answered ({pct}%)
                                        </div>
                                    </div>
                                    <span class="badge badge-terracotta">In Progress</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if st.button("Resume This Examination", key=f"resume_{exam.id}", type="primary"):
                            st.session_state.active_exam_id = exam.id
                            st.session_state.current_question = None
                            st.session_state.last_evaluation = None
                            st.session_state.exam_complete = False
                            st.session_state.current_view = "Examination Room"
                            st.rerun()
        finally:
            db.close()

    # ── TAB 3: HISTORY ────────────────────────────────────────────────────────
    with tab_history:
        st.markdown("### Examination History")
        db = get_db_session()
        try:
            all_exams = (
                db.query(Examination)
                .filter(Examination.user_id == user_id)
                .order_by(Examination.created_at.desc())
                .all()
            )

            if not all_exams:
                st.info("No examination history found.")
            else:
                for exam in all_exams:
                    status_str = exam.status.value if hasattr(exam.status, "value") else str(exam.status)
                    badge_class = "badge-sage" if status_str == "COMPLETED" else "badge-terracotta" if status_str == "IN_PROGRESS" else "badge-sand"
                    doc = db.query(Document).filter(Document.id == exam.document_id).first()
                    doc_title = doc.original_filename if doc else f"Document #{exam.document_id}"

                    with st.expander(f"Exam #{exam.id} — {doc_title} ({status_str})", expanded=False):
                        st.markdown(f"**Started:** {exam.started_at or exam.created_at}")
                        st.markdown(f"**Completed:** {exam.completed_at or 'Incomplete'}")
                        st.markdown(f"**Questions Asked:** {exam.questions_asked_count}/{exam.max_questions}")
                        st.markdown(f"**Current Difficulty Tier:** {exam.current_difficulty.value if hasattr(exam.current_difficulty, 'value') else str(exam.current_difficulty)}")

                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if status_str == "COMPLETED":
                                if st.button("View Examination Report", key=f"rep_{exam.id}"):
                                    st.session_state.selected_report_exam_id = exam.id
                                    st.session_state.current_view = "Examination Reports"
                                    st.rerun()
                            elif status_str == "IN_PROGRESS":
                                if st.button("Resume Session", key=f"res_hist_{exam.id}"):
                                    st.session_state.active_exam_id = exam.id
                                    st.session_state.current_view = "Examination Room"
                                    st.rerun()
        finally:
            db.close()


def _render_active_exam_session(examination_id: int, user_id: int):
    """Renders the active question, timer, answer input, and evaluation feedback."""
    db = get_db_session()
    try:
        exam = (
            db.query(Examination)
            .filter(Examination.id == examination_id, Examination.user_id == user_id)
            .first()
        )
        if not exam:
            st.error("Examination session not found.")
            if st.button("Return to Lobby"):
                st.session_state.active_exam_id = None
                st.rerun()
            return

        doc = db.query(Document).filter(Document.id == exam.document_id).first()
        doc_name = doc.original_filename if doc else f"Document #{exam.document_id}"

        # If exam is already completed
        if exam.status == ExaminationStatus.COMPLETED or st.session_state.get("exam_complete"):
            st.session_state.exam_complete = True
            _render_completion_screen(exam, doc_name)
            return

        # Fetch or hydrate active question
        q_data = st.session_state.get("current_question")
        if not q_data:
            with st.spinner("Autonomous Examiner preparing question..."):
                try:
                    next_q = ExaminationService.start_or_resume_examination(db, exam)
                    if next_q.is_last and next_q.question_asked_id == -1:
                        st.session_state.exam_complete = True
                        st.rerun()
                    st.session_state.current_question = next_q
                    q_data = next_q
                except Exception as exc:
                    st.error(f"Error loading question: {exc}")
                    if st.button("Return to Lobby"):
                        st.session_state.active_exam_id = None
                        st.rerun()
                    return
    finally:
        db.close()

    # Examination Header
    pct = round((exam.questions_asked_count / exam.max_questions) * 100) if exam.max_questions > 0 else 0
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
                <span class="badge badge-terracotta">Live Oral Examination</span>
                <h2 style="font-size: 24px; margin: 4px 0;">{doc_name}</h2>
                <div style="color: var(--color-warmgray); font-size: 13px;">
                    Question {exam.questions_asked_count + 1} of {exam.max_questions} • Topic: <strong>{getattr(q_data, 'topic_name', 'General')}</strong>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge badge-sage">Exam #{exam.id}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(pct / 100.0)

    # Active Question Box
    diff_val = getattr(q_data, "difficulty", "MEDIUM")
    cat_val = getattr(q_data, "category", "CONCEPTUAL")
    is_follow_up = getattr(q_data, "is_follow_up", False)

    follow_up_banner = ""
    if is_follow_up:
        follow_up_banner = '<span class="badge badge-terracotta" style="margin-right: 6px;">Adaptive Follow-Up Probe</span>'

    st.markdown(
        f"""
        <div class="question-banner">
            <div style="margin-bottom: 8px;">
                {follow_up_banner}
                <span class="badge badge-sand">{cat_val}</span>
                <span class="badge badge-sage">{diff_val}</span>
            </div>
            <div class="question-text">
                {getattr(q_data, 'question_text', 'No question text available.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show Previous Granite Evaluation Feedback if available
    last_eval = st.session_state.get("last_evaluation")
    if last_eval:
        with st.expander("📝 Previous Answer Evaluation (IBM Granite watsonx.ai)", expanded=False):
            score_pct = round(last_eval.get("overall_score", 0.0) * 100)
            eval_label = last_eval.get("evaluation_label", "EVALUATED")
            lbl_badge = "badge-sage" if "CORRECT" in eval_label else "badge-terracotta"
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span class="badge {lbl_badge}">{eval_label}</span>
                    <strong style="font-size: 16px;">Overall Score: {score_pct}%</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Scores row
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Correctness (30%)", f"{round(last_eval.get('correctness_score', 0)*100)}%")
            sc2.metric("Completeness (25%)", f"{round(last_eval.get('completeness_score', 0)*100)}%")
            sc3.metric("Conceptual (20%)", f"{round(last_eval.get('conceptual_score', 0)*100)}%")
            sc4.metric("Reasoning (15%)", f"{round(last_eval.get('reasoning_score', 0)*100)}%")
            sc5.metric("Application (10%)", f"{round(last_eval.get('application_score', 0)*100)}%")

            if last_eval.get("evaluation_explanation"):
                st.markdown(f"**Granite Evaluation Analysis:**\n> {last_eval['evaluation_explanation']}")

            if last_eval.get("missing_concepts"):
                st.markdown("**Missing Concepts Identified:**")
                for c in last_eval["missing_concepts"]:
                    st.markdown(f"- ⚠️ {c}")

    # Answer Input Form with Double-Submission Guard
    st.markdown("### Your Response")
    st.caption("Provide a thorough academic answer. Demonstrate conceptual understanding and reasoning.")

    # Track start time for question telemetry
    q_start_key = f"q_start_time_{getattr(q_data, 'question_asked_id', -1)}"
    if q_start_key not in st.session_state:
        st.session_state[q_start_key] = time.time()

    with st.form("answer_submission_form", clear_on_submit=True):
        student_answer = st.text_area(
            "Write your detailed answer below:",
            height=180,
            placeholder="Type your explanation, definitions, proof steps, or formulas here...",
        )
        col_sub1, col_sub2 = st.columns([1, 4])
        with col_sub1:
            submit_btn = st.form_submit_button("Submit Response", type="primary", use_container_width=True)

        if submit_btn:
            if not student_answer or not student_answer.strip():
                st.error("Please enter your answer before submitting.")
            else:
                elapsed = int(time.time() - st.session_state.get(q_start_key, time.time()))
                qa_id = getattr(q_data, "question_asked_id", -1)

                with st.spinner("Submitting to IBM Granite for 5-criterion semantic evaluation..."):
                    db = get_db_session()
                    try:
                        exam_record = db.query(Examination).filter(Examination.id == examination_id).first()
                        payload = SubmitAnswerRequest(
                            question_asked_id=qa_id,
                            answer_text=student_answer.strip(),
                            time_taken_seconds=elapsed,
                        )
                        next_question = ExaminationService.submit_answer_and_advance(
                            db=db,
                            examination=exam_record,
                            payload=payload,
                        )

                        # Load evaluation details from DB
                        last_answer = (
                            db.query(StudentAnswer)
                            .filter(StudentAnswer.question_asked_id == qa_id)
                            .first()
                        )
                        if last_answer and last_answer.evaluation:
                            ev = last_answer.evaluation
                            st.session_state.last_evaluation = {
                                "evaluation_label": ev.evaluation_label.value if hasattr(ev.evaluation_label, "value") else str(ev.evaluation_label),
                                "overall_score": ev.overall_score,
                                "correctness_score": ev.correctness_score or 0.0,
                                "completeness_score": ev.completeness_score or 0.0,
                                "conceptual_score": ev.conceptual_score or 0.0,
                                "reasoning_score": ev.reasoning_score or 0.0,
                                "application_score": ev.application_score or 0.0,
                                "missing_concepts": ev.missing_concepts or [],
                                "mistakes_identified": ev.mistakes_identified or [],
                                "evaluation_explanation": ev.evaluation_explanation or "",
                            }

                        if next_question.is_last and next_question.question_asked_id == -1:
                            st.session_state.exam_complete = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = next_question

                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error submitting response: {exc}")
                    finally:
                        db.close()

    # Session Controls (Finish Early or Abandon)
    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, _ = st.columns([1, 1, 3])
    with c_btn1:
        if st.button("Complete Early & Synthesize Report", use_container_width=True):
            db = get_db_session()
            try:
                exam_record = db.query(Examination).filter(Examination.id == examination_id).first()
                with st.spinner("Synthesizing final academic performance report..."):
                    ExaminationService.manual_complete(db, exam_record)
                st.session_state.exam_complete = True
                st.rerun()
            finally:
                db.close()

    with c_btn2:
        if st.button("Abandon Session", use_container_width=True):
            db = get_db_session()
            try:
                exam_record = db.query(Examination).filter(Examination.id == examination_id).first()
                if exam_record:
                    exam_record.status = ExaminationStatus.ABANDONED
                    db.commit()
                st.session_state.active_exam_id = None
                st.session_state.current_question = None
                st.session_state.current_view = "Examinations"
                st.rerun()
            finally:
                db.close()


def _render_completion_screen(exam: Examination, doc_name: str):
    """Displays completion feedback and direct link to generated report."""
    st.markdown(
        f"""
        <div class="editorial-card" style="text-align: center; padding: 40px; margin-top: 20px;">
            <div style="font-size: 48px; margin-bottom: 12px;">🎓</div>
            <h1 style="font-size: 32px; margin-bottom: 8px;">Examination Complete</h1>
            <p style="color: var(--color-warmgray); font-size: 15px; max-width: 600px; margin: 0 auto 24px auto;">
                Every submitted answer has been semantically evaluated by IBM Granite. Google Gemini has synthesized your verified academic performance report.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("View Comprehensive Academic Report", type="primary", use_container_width=True):
            st.session_state.selected_report_exam_id = exam.id
            st.session_state.active_exam_id = None
            st.session_state.exam_complete = False
            st.session_state.current_view = "Examination Reports"
            st.rerun()

    with col2:
        if st.button("Return to Examination Dashboard", use_container_width=True):
            st.session_state.active_exam_id = None
            st.session_state.exam_complete = False
            st.session_state.current_view = "Dashboard"
            st.rerun()
