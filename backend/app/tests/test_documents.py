"""
Tests for document endpoints and service logic.
Executes endpoint handlers directly with an isolated in-memory SQLite database.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.documents import get_document, list_documents
from app.database.connection import Base
from app.database.models import Document, DocumentStatus, User
from app.core.security import hash_password


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
    user = User(email="doctest@example.com", name="Doc User", hashed_password=hash_password("docpassword"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_list_documents_empty(db, current_user):
    res = list_documents(skip=0, limit=20, db=db, current_user=current_user)
    assert res.total == 0
    assert len(res.documents) == 0


def test_get_nonexistent_document(db, current_user):
    with pytest.raises(HTTPException) as exc_info:
        get_document(document_id=9999, db=db, current_user=current_user)
    assert exc_info.value.status_code == 404


def test_list_documents_with_records(db, current_user):
    doc = Document(
        user_id=current_user.id,
        filename="test.pdf",
        original_filename="Test Module.pdf",
        file_path="storage/uploads/test.pdf",
        file_size=5000,
        status=DocumentStatus.ANALYZED,
        page_count=10,
        word_count=2000,
    )
    db.add(doc)
    db.commit()

    res = list_documents(skip=0, limit=20, db=db, current_user=current_user)
    assert res.total == 1
    assert res.documents[0].original_filename == "Test Module.pdf"

    retrieved = get_document(document_id=doc.id, db=db, current_user=current_user)
    assert retrieved.id == doc.id
    assert retrieved.status == DocumentStatus.ANALYZED
