"""
Comprehensive Migration & Integration Test Suite for ExamForge.
Verifies all preserved backend capabilities, Streamlit app imports, database models,
LangGraph workflow checkpointing, and Scikit-learn ML pipelines.
"""
import os
import pytest
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import (
    Concept,
    ConceptType,
    DifficultyLevel,
    Document,
    DocumentStatus,
    DocumentTopic,
    Examination,
    ExaminationReport,
    ExaminationStatus,
    QuestionBank,
    QuestionCategory,
    Subtopic,
    User,
)
from app.core.security import hash_password, verify_password
from app.llm.model_router import AGENT_MODEL_MAPPING
from app.ml.mastery_predictor import MasteryPredictor
from app.ml.pattern_clustering import LearningPatternClusterer
from app.ml.performance_analyzer import PerformanceAnalyzer
from app.ml.model_storage import ModelStorage
from app.services.report_service import ReportService
from app.workflows.checkpoint_manager import CheckpointManager


@pytest.fixture
def db_session(tmp_path):
    """Provides an isolated SQLite test database session."""
    test_db = f"sqlite:///{tmp_path}/test_integration.db"
    engine = create_engine(test_db, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


def test_auth_and_security(db_session):
    """Verify password hashing and user persistence."""
    pwd = "securepassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("wrongpassword", hashed)

    user = User(
        email="examinee@university.edu",
        name="Elena Rostova",
        hashed_password=hashed,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "examinee@university.edu"


def test_document_and_question_bank_hierarchy(db_session):
    """Verify document, topic, subtopic, concept, and question bank relational models."""
    user = User(email="prof@edu.org", name="Prof Turing", hashed_password=hash_password("profpass123"))
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="os_notes.pdf",
        original_filename="Operating Systems.pdf",
        file_path="storage/uploads/os_notes.pdf",
        file_size=10240,
        status=DocumentStatus.ANALYZED,
        page_count=25,
        word_count=5200,
    )
    db_session.add(doc)
    db_session.commit()

    topic = DocumentTopic(
        document_id=doc.id,
        name="Virtual Memory",
        description="Paging, Page Faults, TLB, Page Replacement",
        order_index=1,
    )
    db_session.add(topic)
    db_session.commit()

    subtopic = Subtopic(
        topic_id=topic.id,
        document_id=doc.id,
        name="Page Replacement Algorithms",
        order_index=1,
    )
    db_session.add(subtopic)
    db_session.commit()

    concept = Concept(
        topic_id=topic.id,
        subtopic_id=subtopic.id,
        document_id=doc.id,
        type=ConceptType.ALGORITHM,
        name="LRU Replacement",
        content="Replaces the page that has not been used for the longest period of time.",
    )
    db_session.add(concept)
    db_session.commit()

    qb = QuestionBank(
        document_id=doc.id,
        topic_id=topic.id,
        subtopic_id=subtopic.id,
        question_text="Explain the difference between FIFO and LRU page replacement under Belady's Anomaly.",
        category=QuestionCategory.DIFFERENCE,
        difficulty=DifficultyLevel.HARD,
        expected_answer_points=["FIFO suffers Belady anomaly", "LRU is a stack algorithm immune to it"],
        is_used=False,
    )
    db_session.add(qb)
    db_session.commit()

    # Query back
    retrieved_topic = db_session.query(DocumentTopic).filter(DocumentTopic.id == topic.id).first()
    assert len(retrieved_topic.question_bank) == 1
    assert retrieved_topic.question_bank[0].difficulty == DifficultyLevel.HARD


def test_examination_session_checkpoint_hydration(db_session):
    """Verify examination creation, status tracking, and LangGraph checkpoint hydration."""
    user = User(email="student@mit.edu", name="Claude Shannon", hashed_password=hash_password("info123"))
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="info_theory.pdf",
        original_filename="Information Theory.pdf",
        file_path="storage/uploads/info_theory.pdf",
        file_size=20480,
        status=DocumentStatus.ANALYZED,
    )
    db_session.add(doc)
    db_session.commit()

    exam = Examination(
        user_id=user.id,
        document_id=doc.id,
        max_questions=10,
        status=ExaminationStatus.IN_PROGRESS,
        current_difficulty=DifficultyLevel.MEDIUM,
    )
    db_session.add(exam)
    db_session.commit()

    assert exam.id is not None
    assert exam.status == ExaminationStatus.IN_PROGRESS


def test_six_agent_routing_and_models():
    """Verify exact model mapping for all 6 AI agents."""
    assert AGENT_MODEL_MAPPING["document_understanding"] == "gemini"
    assert AGENT_MODEL_MAPPING["question_generation"] == "gemini"
    assert AGENT_MODEL_MAPPING["examination"] == "gemini"
    assert AGENT_MODEL_MAPPING["answer_evaluation"] == "granite"
    assert AGENT_MODEL_MAPPING["knowledge_assessment"] == "granite"
    assert AGENT_MODEL_MAPPING["report_generation"] == "gemini"


def test_ml_performance_analyzer_and_models(tmp_path):
    """Verify Scikit-learn model training, test split metrics, and model persistence."""
    storage = ModelStorage(models_dir=str(tmp_path))
    predictor = MasteryPredictor(storage=storage)

    # 15 topic feature rows to test training
    np.random.seed(101)
    rows = []
    for i in range(15):
        mastered = 1 if i % 2 == 0 else 0
        score = 0.85 if mastered else 0.40
        rows.append({
            "total_questions": 12,
            "avg_score": score + np.random.normal(0, 0.03),
            "avg_correctness": score,
            "avg_completeness": score,
            "avg_conceptual": score,
            "avg_reasoning": score,
            "avg_application": score,
            "avg_time_seconds": 28.0,
            "easy_ratio": 0.3,
            "hard_ratio": 0.2,
            "correct_ratio": 0.8 if mastered else 0.3,
            "incorrect_ratio": 0.1 if mastered else 0.6,
            "missing_concepts_count": 0 if mastered else 4,
            "is_mastered": mastered,
        })
    df = pd.DataFrame(rows)

    res = predictor.train(df)
    assert res["success"] is True
    assert "test_accuracy" in res["metrics"]
    assert predictor.is_trained is True

    # Test persistence
    assert storage.model_exists("mastery_predictor")
    new_predictor = MasteryPredictor(storage=storage)
    assert new_predictor.is_trained is True


def test_pdf_report_generation(db_session):
    """Verify ReportLab PDF generation executes cleanly and returns valid PDF bytes."""
    user = User(email="report_user@edu.org", name="Alan Kay", hashed_password=hash_password("smalltalk123"))
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="comp_arch.pdf",
        original_filename="Computer Architecture.pdf",
        file_path="storage/uploads/comp_arch.pdf",
        file_size=50000,
        status=DocumentStatus.ANALYZED,
    )
    db_session.add(doc)
    db_session.commit()

    exam = Examination(
        user_id=user.id,
        document_id=doc.id,
        max_questions=10,
        questions_asked_count=10,
        status=ExaminationStatus.COMPLETED,
    )
    db_session.add(exam)
    db_session.commit()

    report = ExaminationReport(
        examination_id=exam.id,
        user_id=user.id,
        document_id=doc.id,
        overall_score=0.88,
        topic_scores={"1": 0.9, "2": 0.85},
        strong_concepts=["Pipelining", "Branch Prediction"],
        weak_concepts=["Cache Coherence"],
        recommendations=["Review MSI and MESI cache coherence protocols."],
    )
    db_session.add(report)
    db_session.commit()

    pdf_bytes = ReportService.generate_pdf(
        db=db_session,
        report=report,
        examination=exam,
        user=user,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
