"""
Tests for auth endpoints and security logic.
Executes endpoint handlers directly with an isolated in-memory SQLite database.
"""
import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import login, me, register
from app.database.connection import Base
from app.database.models import User
from app.schemas.auth import RegisterRequest


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


def test_register_user(db):
    payload = RegisterRequest(email="test@example.com", name="Test User", password="password123")
    res = register(payload, db)
    assert res.access_token is not None
    assert res.token_type == "bearer"

    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.name == "Test User"


def test_register_duplicate_email(db):
    payload1 = RegisterRequest(email="dup@example.com", name="User A", password="passA123")
    register(payload1, db)

    payload2 = RegisterRequest(email="dup@example.com", name="User B", password="passB123")
    with pytest.raises(HTTPException) as exc_info:
        register(payload2, db)
    assert exc_info.value.status_code == 409


def test_register_short_password():
    """Passwords shorter than 6 characters must be rejected by Pydantic schema."""
    with pytest.raises(Exception):
        RegisterRequest(email="short@example.com", name="Short Pwd", password="abc")


def test_login_success(db):
    register(RegisterRequest(email="login@example.com", name="Login User", password="mypassword"), db)
    form_data = OAuth2PasswordRequestForm(
        grant_type="password",
        username="login@example.com",
        password="mypassword",
        scope="",
        client_id=None,
        client_secret=None,
    )
    res = login(form_data, db)
    assert res.access_token is not None


def test_login_wrong_password(db):
    register(RegisterRequest(email="wp@example.com", name="WP", password="correct123"), db)
    form_data = OAuth2PasswordRequestForm(
        grant_type="password",
        username="wp@example.com",
        password="wrongpassword",
        scope="",
        client_id=None,
        client_secret=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        login(form_data, db)
    assert exc_info.value.status_code == 401


def test_login_unknown_user(db):
    form_data = OAuth2PasswordRequestForm(
        grant_type="password",
        username="nobody@example.com",
        password="doesnotmatter",
        scope="",
        client_id=None,
        client_secret=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        login(form_data, db)
    assert exc_info.value.status_code == 401


def test_me_endpoint(db):
    register(RegisterRequest(email="me@example.com", name="Me User", password="mepassword"), db)
    user = db.query(User).filter(User.email == "me@example.com").first()
    profile = me(current_user=user)
    assert profile.email == "me@example.com"
    assert profile.name == "Me User"
