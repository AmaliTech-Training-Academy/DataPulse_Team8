"""Reports router - IMPLEMENTED."""

import csv
from io import StringIO
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.report import QualityReport, QualityTrendResponse
from app.models.dataset import Dataset
from app.models.user import User
from app.services import report_service
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.get("/trends", response_model=QualityTrendResponse)
def get_quality_trends(
    dataset_id: Optional[int] = Query(None, description="Optional dataset ID filter"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    interval: str = Query("day", description="Aggregation interval (day, week, month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality score trends over time."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    end_date = datetime.now(timezone.utc)

    if interval not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400, detail="Invalid interval. Use 'day', 'week', or 'month'"
        )

    trend_data = report_service.get_trend_data(
        dataset_id, start_date, end_date, interval, db, current_user
    )
    return trend_data


@router.get("/{dataset_id}", response_model=QualityReport)
def get_dataset_report(
    dataset_id: int,
    format: Optional[str] = Query("json", description="format json or csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a full quality report for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.uploaded_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")

    report = report_service.generate_report(dataset_id, db)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for dataset")

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(["Executive Summary"])
        writer.writerow(["Score", report["score"]])
        writer.writerow(["Total Rules", report["total_rules"]])
        writer.writerow(["Passed Rules", report["passed_rules"]])
        writer.writerow(["Failed Rules", report["failed_rules"]])
        writer.writerow([])

        writer.writerow(["Detailed Findings"])
        writer.writerow(["Rule ID", "Passed", "Failed Rows", "Total Rows", "Details"])
        for res in report["results"]:
            writer.writerow(
                [
                    res.rule_id,
                    res.passed,
                    res.failed_rows,
                    res.total_rows,
                    res.details or "",
                ]
            )

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=report_{dataset_id}.csv"
            },
        )

    return report
