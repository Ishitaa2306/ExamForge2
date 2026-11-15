"""
Document Upload, Analysis & Knowledge Map View.
Handles PDF processing, ChromaDB semantic vectorization, Gemini curriculum deconstruction,
and hierarchical knowledge tree visualization.
"""
import os
import uuid
from datetime import datetime, timezone
import streamlit as st

from app.core.config import settings
from app.database.models import (
    Concept,
    Document,
    DocumentStatus,
    DocumentTopic,
    Subtopic,
)
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PDFService
from streamlit_app.state import get_current_user_id, get_db_session


def render_documents_view():
    user_id = get_current_user_id()
    if not user_id:
        st.warning("Please sign in to access documents.")
        return

    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">Agent 1: Document Understanding</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Curriculum Document Analysis</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Upload academic syllabi, textbook chapters, or lecture notes. Google Gemini extracts topics, subtopics, formulas, and definitions, grounding the question bank in ChromaDB.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_upload, tab_library, tab_map = st.tabs(["Upload New PDF", "Document Library", "Knowledge Map"])

    # ── TAB 1: UPLOAD ─────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown("### Upload Curriculum Module")
        uploaded_file = st.file_uploader(
            "Select an academic PDF (Max 50MB)",
            type=["pdf"],
            help="Digital or scanned PDF files supported.",
        )

        if uploaded_file is not None:
            # File validation
            file_bytes = uploaded_file.getvalue()
            file_size_mb = len(file_bytes) / (1024 * 1024)

            if file_size_mb > settings.MAX_FILE_SIZE_MB:
                st.error(f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB} MB.")
            elif not uploaded_file.name.lower().endswith(".pdf"):
                st.error("Only PDF documents are supported.")
            else:
                st.info(f"Ready to process: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")

                if st.button("Process & Analyze Document", type="primary"):
                    with st.spinner("Processing PDF and extracting curriculum structure..."):
                        # Ensure storage directories
                        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                        os.makedirs(settings.CHROMA_DIR, exist_ok=True)

                        # Save file to disk
                        unique_filename = f"{uuid.uuid4().hex}_{uploaded_file.name}"
                        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
                        with open(file_path, "wb") as f:
                            f.write(file_bytes)

                        # Create Document record
                        db = get_db_session()
                        try:
                            doc = Document(
                                user_id=user_id,
                                filename=unique_filename,
                                original_filename=uploaded_file.name,
                                file_path=file_path,
                                file_size=len(file_bytes),
                                status=DocumentStatus.UPLOADED,
                            )
                            db.add(doc)
                            db.commit()
                            db.refresh(doc)
                            doc_id = doc.id
                        finally:
                            db.close()

                        # Run analysis pipeline
                        try:
                            # Step 1: Text extraction
                            st.text("Step 1/4: Extracting text with PyMuPDF...")
                            text_pages = PDFService.extract_text(file_path)
                            if not text_pages:
                                raise ValueError("Could not extract any readable text from this PDF.")

                            # Step 2: Semantic embedding
                            st.text("Step 2/4: Chunking and indexing into ChromaDB...")
                            db = get_db_session()
                            try:
                                doc_record = db.query(Document).filter(Document.id == doc_id).first()
                                EmbeddingService.embed_document(db=db, document=doc_record, text_pages=text_pages)
                            finally:
                                db.close()

                            # Step 3: Gemini Document Understanding
                            st.text("Step 3/4: Google Gemini analyzing topics, subtopics, and concepts...")
                            from app.agents.document_understanding import DocumentUnderstandingAgent
                            db = get_db_session()
                            try:
                                structure = DocumentUnderstandingAgent.analyse(
                                    document_id=doc_id,
                                    text_pages=text_pages,
                                    db=db,
                                )
                            finally:
                                db.close()

                            # Step 4: Gemini Question Generation
                            st.text("Step 4/4: Google Gemini generating grounded question bank...")
                            from app.agents.question_generation import QuestionGenerationAgent
                            db = get_db_session()
                            try:
                                QuestionGenerationAgent.generate(
                                    document_id=doc_id,
                                    structure=structure,
                                    db=db,
                                )
                                # Update completion status
                                doc_record = db.query(Document).filter(Document.id == doc_id).first()
                                doc_record.page_count = len(text_pages)
                                doc_record.word_count = sum(len(p.split()) for p in text_pages)
                                doc_record.status = DocumentStatus.ANALYZED
                                doc_record.analyzed_at = datetime.now(timezone.utc)
                                db.commit()
                            finally:
                                db.close()

                            st.success(f"Analysis complete! Extracted {len(structure.get('topics', []))} topics and generated grounded questions.")
                            st.session_state.selected_doc_id = doc_id
                            st.rerun()

                        except Exception as exc:
                            db = get_db_session()
                            try:
                                doc_record = db.query(Document).filter(Document.id == doc_id).first()
                                if doc_record:
                                    doc_record.status = DocumentStatus.FAILED
                                    db.commit()
                            finally:
                                db.close()
                            st.error(f"Document analysis encountered an error: {exc}")

    # ── TAB 2: LIBRARY ────────────────────────────────────────────────────────
    with tab_library:
        st.markdown("### Analyzed Documents")
        db = get_db_session()
        try:
            docs = (
                db.query(Document)
                .filter(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
                .all()
            )
        finally:
            db.close()

        if not docs:
            st.info("No documents uploaded yet.")
        else:
            for doc in docs:
                status_str = doc.status.value if hasattr(doc.status, "value") else str(doc.status)
                badge_class = "badge-sage" if status_str == "ANALYZED" else "badge-terracotta" if status_str == "FAILED" else "badge-sand"

                with st.expander(f"{doc.original_filename} ({status_str})", expanded=False):
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.caption(f"Pages: {doc.page_count or 0}")
                    with col_info2:
                        st.caption(f"Words: {doc.word_count or 0}")
                    with col_info3:
                        st.caption(f"Status: {status_str}")

                    col_btn1, col_btn2 = st.columns([1, 1])
                    with col_btn1:
                        if st.button("Explore Knowledge Map", key=f"btn_map_{doc.id}"):
                            st.session_state.selected_doc_id = doc.id
                            st.rerun()
                    with col_btn2:
                        if st.button("Browse Question Bank", key=f"btn_qb_{doc.id}"):
                            st.session_state.selected_doc_id = doc.id
                            st.session_state.current_view = "Question Bank"
                            st.rerun()

    # ── TAB 3: KNOWLEDGE MAP ──────────────────────────────────────────────────
    with tab_map:
        st.markdown("### Hierarchical Knowledge Map")
        db = get_db_session()
        try:
            user_docs = db.query(Document).filter(Document.user_id == user_id).all()
            doc_options = {d.id: d.original_filename for d in user_docs if d.status == DocumentStatus.ANALYZED}
        finally:
            db.close()

        if not doc_options:
            st.info("No analyzed documents available. Upload and analyze a document first.")
        else:
            default_id = st.session_state.get("selected_doc_id")
            if default_id not in doc_options:
                default_id = list(doc_options.keys())[0]

            selected_id = st.selectbox(
                "Select Document",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options[x],
                index=list(doc_options.keys()).index(default_id) if default_id in doc_options else 0,
            )

            db = get_db_session()
            try:
                topics = (
                    db.query(DocumentTopic)
                    .filter(DocumentTopic.document_id == selected_id)
                    .order_by(DocumentTopic.order_index.asc())
                    .all()
                )

                if not topics:
                    st.info("No extracted topics found for this document.")
                else:
                    for topic in topics:
                        st.markdown(
                            f"""
                            <div class="editorial-card" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <h3 style="font-size: 18px; margin: 0;">Topic: {topic.name}</h3>
                                    <span class="badge badge-sand">Pages {topic.page_start or 1}–{topic.page_end or 'end'}</span>
                                </div>
                                <p style="color: var(--color-warmgray); font-size: 13px; margin-top: 6px;">
                                    {topic.description or 'No topic description provided.'}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Subtopics
                        subtopics = (
                            db.query(Subtopic)
                            .filter(Subtopic.topic_id == topic.id)
                            .order_by(Subtopic.order_index.asc())
                            .all()
                        )
                        if subtopics:
                            with st.container():
                                for sub in subtopics:
                                    st.markdown(f"- **Subtopic:** {sub.name} — *{sub.description or ''}*")

                        # Concepts (Definitions, Formulas, Algorithms)
                        concepts = (
                            db.query(Concept)
                            .filter(Concept.topic_id == topic.id)
                            .all()
                        )
                        if concepts:
                            cols = st.columns(min(len(concepts), 3))
                            for idx, c in enumerate(concepts):
                                col_idx = idx % min(len(concepts), 3)
                                with cols[col_idx]:
                                    c_type = c.type.value if hasattr(c.type, "value") else str(c.type)
                                    badge_type = "badge-sage" if c_type == "DEFINITION" else "badge-terracotta" if c_type == "FORMULA" else "badge-olive"
                                    st.markdown(
                                        f"""
                                        <div style="background: #FFFFFF; border: 1px solid var(--color-sand); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                            <span class="badge {badge_type}">{c_type}</span>
                                            <div style="font-weight: 600; font-size: 13px; margin-top: 4px;">{c.name}</div>
                                            <div style="font-size: 12px; color: var(--color-charcoal); margin-top: 2px;">{c.content}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
            finally:
                db.close()
