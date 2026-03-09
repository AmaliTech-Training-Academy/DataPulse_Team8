"""
conftest.py — Shared fixtures for the DataPulse pytest suite.
"""

import io
import json
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_datapulse.db")
connect_args = {"check_same_thread": False} if SQLALCHEMY_TEST_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args=connect_args)
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
    if SQLALCHEMY_TEST_URL.startswith("sqlite"):
        db_path = SQLALCHEMY_TEST_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def test_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# ── Auth fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def registered_user(client):
    resp = client.post("/api/auth/register", json={
        "email": "qa_user@datapulse.com",
        "password": "qapassword123",
        "full_name": "QA Tester"
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture(scope="session")
def auth_token(registered_user):
    return registered_user["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ── CSV / JSON test content ───────────────────────────────────────────────────

CLEAN_CSV = (
    "id,name,email,age,score\n"
    "1,Alice,alice@test.com,30,85\n"
    "2,Bob,bob@test.com,28,92\n"
    "3,Carol,carol@test.com,35,78\n"
    "4,David,david@test.com,42,88\n"
    "5,Eve,eve@test.com,26,95\n"
)

DIRTY_CSV = (
    "id,name,email,age,score\n"
    "1,,alice@test.com,30,85\n"
    "2,Bob,not-email,-5,\n"
    "3,Carol,carol@test.com,abc,78\n"
    "4,,david@test.com,42,88\n"
    "5,Eve,,26,150\n"
)

MIXED_CSV = (
    "id,name,email,age,score\n"
    "1,Alice,alice@test.com,30,85\n"
    "2,Bob,bob@test.com,28,92\n"
    "3,,carol@test.com,35,78\n"
    "4,David,david@test.com,42,88\n"
    "5,Eve,eve@test.com,200,95\n"
)

VALID_JSON = json.dumps([
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob",   "age": 25},
    {"id": 3, "name": "Carol", "age": 35},
])


def csv_file(content, filename="test.csv"):
    return {"file": (filename, io.BytesIO(content.encode()), "text/csv")}


def json_file(content, filename="test.json"):
    return {"file": (filename, io.BytesIO(content.encode()), "application/json")}


# ── Dataset fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def uploaded_csv(client):
    resp = client.post("/api/datasets/upload", files=csv_file(CLEAN_CSV, "clean.csv"))
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def uploaded_dirty_csv(client):
    resp = client.post("/api/datasets/upload", files=csv_file(DIRTY_CSV, "dirty.csv"))
    assert resp.status_code == 201
    return resp.json()


# ── Rule payload helpers ──────────────────────────────────────────────────────

def not_null_rule(field="name", severity="HIGH"):
    return {"name": f"no_nulls_{field}", "dataset_type": "csv",
            "field_name": field, "rule_type": "NOT_NULL", "severity": severity}


def data_type_rule(field="age", expected_type="int", severity="MEDIUM"):
    return {"name": f"type_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "DATA_TYPE", "parameters": json.dumps({"expected_type": expected_type}),
            "severity": severity}


def range_rule(field="score", min_val=0, max_val=100, severity="MEDIUM"):
    return {"name": f"range_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "RANGE", "parameters": json.dumps({"min": min_val, "max": max_val}),
            "severity": severity}


def unique_rule(field="id", severity="HIGH"):
    return {"name": f"unique_{field}", "dataset_type": "csv",
            "field_name": field, "rule_type": "UNIQUE", "severity": severity}


def regex_rule(field="email", pattern=r"^[\w.+-]+@[\w-]+\.\w+$", severity="LOW"):
    return {"name": f"regex_{field}", "dataset_type": "csv", "field_name": field,
            "rule_type": "REGEX", "parameters": json.dumps({"pattern": pattern}),
            "severity": severity}
