import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture for TestClient."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Fixture for test database."""
    # This would typically set up a test database
    # For now, it's a placeholder
    pass
