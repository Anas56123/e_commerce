"""
Shared pytest fixtures for the e-commerce API test suite.

Uses an in-memory SQLite database so tests never touch production Postgres.
"""
import sys
import os

# Make sure the project root is on PYTHONPATH so all imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# --------------------------------------------------------------------------- #
#  In-memory SQLite engine (isolated per test session)                        #
# --------------------------------------------------------------------------- #
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test/test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create all tables before the test session and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    """Return a TestClient that shares a single DB across the session."""
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
#  Reusable helpers to register users and obtain JWT tokens                   #
# --------------------------------------------------------------------------- #

def register_and_login(client: TestClient, username: str, email: str, password: str, role: str = "student") -> str:
    """Register a user (if not already existing) and return a Bearer token."""
    client.post(
        "/register",
        data={"username": username, "email": email, "password": password, "role": role},
    )
    resp = client.post(
        "/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(client):
    return register_and_login(client, "test_student", "student@test.com", "testpass123", "student")


@pytest.fixture(scope="session")
def instructor_token(client):
    return register_and_login(client, "test_instructor", "instructor@test.com", "testpass123", "instructor")


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
