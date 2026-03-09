"""Reports router - FULLY IMPLEMENTED."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.report import QualityReport, QualityScoreResponse
from app.services.report_service import generate_report, get_trend_data

router = APIRouter()


@router.get("/trends", response_model=list[QualityScoreResponse])
def get_quality_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get quality score trends over the past N days (default 30)."""
    scores = get_trend_data(days, db)
    return scores


@router.get("/{dataset_id}", response_model=QualityReport)
def get_dataset_report(dataset_id: int, db: Session = Depends(get_db)):
    """Get a full quality report for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    report = generate_report(dataset_id, db)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No quality checks have been run for dataset {dataset_id} yet. "
                   f"Run POST /api/checks/run/{dataset_id} first.",
        )
    return report
