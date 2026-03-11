"""Test fixtures for pytest."""

import os

os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.main import app  # noqa: E402

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    from app.routers.checks import request_counts

    request_counts.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(client):
    email = "test@example.com"
    password = "Password123"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    if resp.status_code == 400 and "already registered" in resp.text:
        resp = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
    return resp.json()


@pytest.fixture
def auth_token(sample_user):
    return sample_user["access_token"]


@pytest.fixture
def admin_user(client, test_db):
    email = "admin@example.com"
    password = "AdminPassword123"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Admin User"},
    )
    if resp.status_code == 400 and "already registered" in resp.text:
        resp = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )

    # Make the user admin in the DB
    from app.models.user import User

    admin_db_user = test_db.query(User).filter(User.email == email).first()
    if admin_db_user and not admin_db_user.is_admin:
        admin_db_user.is_admin = True
        test_db.commit()

    return resp.json()


@pytest.fixture
def admin_token(admin_user):
    return admin_user["access_token"]
