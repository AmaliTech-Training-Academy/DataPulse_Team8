"""Unit tests for the Quality Trends generation."""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from app.models.check_result import QualityScore
from app.models.dataset import Dataset
from app.models.user import User
from app.services.report_service import get_trend_data

@pytest.fixture
def mock_dataset(test_db):
    user = User(email=f"trend_test_{uuid.uuid4()}@test.com", hashed_password="pw", full_name="Trend Tester")
    test_db.add(user)
    test_db.commit()
    
    ds = Dataset(name="trend_ds.csv", file_type="csv", uploaded_by=user.id, row_count=100)
    test_db.add(ds)
    test_db.commit()
    
    return ds

def test_trend_aggregation_direction_up(test_db, mock_dataset):
    """Test trend calculations for increasing scores."""
    now = datetime.now(timezone.utc)
    
    # Add an upward trend over 3 days
    test_db.add(QualityScore(dataset_id=mock_dataset.id, score=60.0, total_rules=5, passed_rules=3, failed_rules=2, checked_at=now - timedelta(days=2)))
    test_db.add(QualityScore(dataset_id=mock_dataset.id, score=70.0, total_rules=5, passed_rules=3, failed_rules=2, checked_at=now - timedelta(days=1)))
    test_db.add(QualityScore(dataset_id=mock_dataset.id, score=85.0, total_rules=5, passed_rules=4, failed_rules=1, checked_at=now))
    test_db.commit()

    trend = get_trend_data(
        dataset_id=mock_dataset.id, 
        start_date=now - timedelta(days=5), 
        end_date=now + timedelta(days=1), 
        interval="day", 
        db=test_db
    )
    
    assert trend["dataset_id"] == mock_dataset.id
    assert trend["trend_direction"] == "up"  # Should identify upward push
    assert len(trend["trend_data"]) == 3
    
    # 60+70+85 / 3 = 71.67
    assert 71.6 <= trend["average_score"] <= 71.7

def test_trend_aggregation_direction_down(test_db, mock_dataset):
    """Test trend calculations for decreasing scores."""
    now = datetime.now(timezone.utc)
    
    # Add a downward trend over 2 days
    test_db.add(QualityScore(dataset_id=mock_dataset.id, score=90.0, total_rules=5, passed_rules=5, failed_rules=0, checked_at=now - timedelta(days=1)))
    test_db.add(QualityScore(dataset_id=mock_dataset.id, score=40.0, total_rules=5, passed_rules=2, failed_rules=3, checked_at=now))
    test_db.commit()

    trend = get_trend_data(
        dataset_id=mock_dataset.id, 
        start_date=now - timedelta(days=3), 
        end_date=now + timedelta(days=1), 
        interval="day", 
        db=test_db
    )
    
    assert trend["trend_direction"] == "down"  # Score dropped heavily
    assert trend["average_score"] == 65.0

def test_trend_aggregation_direction_flat(test_db, mock_dataset):
    """Test trend calculations for steady state."""
    now = datetime.now(timezone.utc)
    
    # Flat trend over 4 days
    for i in range(4):
        test_db.add(QualityScore(dataset_id=mock_dataset.id, score=95.0, total_rules=5, passed_rules=5, failed_rules=0, checked_at=now - timedelta(days=i)))
    test_db.commit()

    trend = get_trend_data(
        dataset_id=mock_dataset.id, 
        start_date=now - timedelta(days=7), 
        end_date=now + timedelta(days=1), 
        interval="day", 
        db=test_db
    )
    
    assert trend["trend_direction"] == "flat"  # Score stayed perfectly flat
    assert trend["average_score"] == 95.0
    assert trend["volatility"] == 0.0

def test_trend_aggregation_empty_data(test_db):
    """Test trend behavior when no scores exist."""
    now = datetime.now(timezone.utc)
    trend = get_trend_data(
        dataset_id=9999, 
        start_date=now - timedelta(days=30), 
        end_date=now, 
        interval="month", 
        db=test_db
    )
    
    assert trend["trend_direction"] == "flat"
    assert trend["volatility"] == 0.0
    assert len(trend["trend_data"]) == 0
    assert trend["average_score"] == 0.0
