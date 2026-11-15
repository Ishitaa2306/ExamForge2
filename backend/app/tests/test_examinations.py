"""
Tests for Examination workflow, endpoints, and status checks.
Executes endpoint handlers directly with an isolated in-memory SQLite database.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.examinations import (
    create_examination,
    get_examination,
    list_examinations,
)
from app.api.settings import get_system_status
from app.database.connection import Base
from app.database.models import Document, DocumentStatus, Examination, ExaminationStatus, User
from app.core.security import hash_password
from app.schemas.examinations import ExaminationCreateRequest


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def current_user(db):
    user = User(email="examuser@example.com", name="Exam User", hashed_password=hash_password("exampassword"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_list_examinations_empty(db, current_user):
    res = list_examinations(skip=0, limit=20, db=db, current_user=current_user)
    assert res.total == 0
    assert len(res.examinations) == 0


def test_create_examination_invalid_document(db, current_user):
    payload = ExaminationCreateRequest(document_id=9999, max_questions=10)
    with pytest.raises(HTTPException) as exc_info:
        create_examination(payload=payload, db=db, current_user=current_user)
    assert exc_info.value.status_code == 404


def test_get_nonexistent_examination(db, current_user):
    with pytest.raises(HTTPException) as exc_info:
        get_examination(examination_id=9999, db=db, current_user=current_user)
    assert exc_info.value.status_code == 404


def test_create_and_list_examination(db, current_user):
    # Create analyzed document
    doc = Document(
        user_id=current_user.id,
        filename="distributed.pdf",
        original_filename="Distributed Systems.pdf",
        file_path="storage/uploads/distributed.pdf",
        file_size=12000,
        status=DocumentStatus.ANALYZED,
    )
    db.add(doc)
    db.commit()

    payload = ExaminationCreateRequest(document_id=doc.id, max_questions=15)
    exam = create_examination(payload=payload, db=db, current_user=current_user)
    assert exam.id is not None
    assert exam.max_questions == 15
    assert exam.status == ExaminationStatus.CREATED

    # List examinations
    res = list_examinations(skip=0, limit=20, db=db, current_user=current_user)
    assert res.total == 1
    assert res.examinations[0].id == exam.id


def test_settings_status_endpoint(db, current_user):
    """Settings status returns application, db, and provider info without credentials."""
    data = get_system_status(db=db, current_user=current_user)
    assert "application" in data
    assert "database" in data
    assert "gemini" in data
    assert "granite" in data
    assert data["application"]["name"] == "ExamForge"
