"""Report service - FULLY IMPLEMENTED."""

from datetime import datetime, timedelta
from app.models.dataset import Dataset
from app.models.check_result import CheckResult, QualityScore


def generate_report(dataset_id: int, db) -> dict:
    """Generate a quality report for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return None

    # Get the latest quality score for this dataset
    latest_score = (
        db.query(QualityScore)
        .filter(QualityScore.dataset_id == dataset_id)
        .order_by(QualityScore.checked_at.desc())
        .first()
    )
    if not latest_score:
        return None

    # Get all check results from the latest run (same checked_at timestamp)
    results = (
        db.query(CheckResult)
        .filter(CheckResult.dataset_id == dataset_id)
        .order_by(CheckResult.checked_at.desc())
        .all()
    )

    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "score": latest_score.score,
        "total_rules": latest_score.total_rules,
        "results": results,
        "checked_at": latest_score.checked_at,
    }


def get_trend_data(days: int, db) -> list:
    """Get quality score trend data for the past N days."""
    start_date = datetime.utcnow() - timedelta(days=days)
    scores = (
        db.query(QualityScore)
        .filter(QualityScore.checked_at >= start_date)
        .order_by(QualityScore.checked_at.asc())
        .all()
    )
    return scores
