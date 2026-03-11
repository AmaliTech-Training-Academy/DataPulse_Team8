"""Quality checks router - IMPLEMENTED."""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.check_result import CheckResult, QualityScore
from app.models.dataset import Dataset, DatasetFile
from app.models.rule import ValidationRule
from app.models.user import User
from app.schemas.report import CheckResultResponse
from app.services.file_parser import parse_csv, parse_json
from app.services.scoring_service import calculate_quality_score
from app.services.validation_engine import ValidationEngine
from app.utils.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger("datapulse.checks")

# Simple in-memory rate limiter for maximum 10 checks per minute
request_counts = defaultdict(list)


def check_rate_limit(client_ip: str):
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)

    # Clean up old timestamps
    request_counts[client_ip] = [t for t in request_counts[client_ip] if t > cutoff]

    if len(request_counts[client_ip]) >= 10:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Max 10 checks per minute."
        )

    request_counts[client_ip].append(now)


@router.post("/run/{dataset_id}", status_code=200)
def run_checks(
    dataset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run all applicable validation checks on a dataset."""
    start_time = time.time()

    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.uploaded_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to run checks on this dataset"
        )

    dataset_file = (
        db.query(DatasetFile).filter(DatasetFile.dataset_id == dataset_id).first()
    )
    if not dataset_file:
        raise HTTPException(status_code=404, detail="Dataset file not found")

    file_path = dataset_file.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 100MB")

    try:
        if dataset.file_type == "csv":
            metadata = parse_csv(file_path)
        else:
            metadata = parse_json(file_path)
    except Exception as e:
        dataset.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to load dataset: {str(e)}")

    df = metadata["dataframe"]

    # We load rules filtering out inactive ones
    rules = db.query(ValidationRule).filter(ValidationRule.is_active).all()
    # Filter rules to only include those that match the dataset name or fields present (flexibility)
    rules = [
        r for r in rules if r.dataset_type == dataset.name or r.field_name in df.columns
    ]

    if not rules:
        raise HTTPException(
            status_code=400, detail="No active rules applicable for this dataset"
        )

    engine = ValidationEngine()
    results = engine.run_all_checks(df, rules)

    try:
        # Clear previous records if rerunning checks on the same dataset
        db.query(CheckResult).filter(CheckResult.dataset_id == dataset_id).delete()
        db.query(QualityScore).filter(QualityScore.dataset_id == dataset_id).delete()

        check_records = []
        for res in results:
            record = CheckResult(
                dataset_id=dataset_id,
                rule_id=res["rule_id"],
                passed=res["passed"],
                failed_rows=res["failed_rows"],
                total_rows=res["total_rows"],
                details=res["details"],
            )
            db.add(record)
            check_records.append(record)

        score_data = calculate_quality_score(results, rules)

        quality_score = QualityScore(
            dataset_id=dataset_id,
            score=score_data["score"],
            total_rules=score_data["total_rules"],
            passed_rules=score_data["passed_rules"],
            failed_rules=score_data["failed_rules"],
        )
        db.add(quality_score)

        dataset.status = "VALIDATED"
        db.commit()

        process_time = time.time() - start_time
        logger.info(
            f"Checking dataset {dataset_id} completed in {process_time:.2f}s with score {score_data['score']}"
        )

        return {
            "dataset_id": dataset_id,
            "status": "VALIDATED",
            "score": score_data["score"],
            "results_summary": score_data,
            "execution_time_seconds": round(process_time, 2),
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving validation results: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while saving results"
        )


@router.get("/results/{dataset_id}", response_model=list[CheckResultResponse])
def get_check_results(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all check results for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.uploaded_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to view these results"
        )

    results = (
        db.query(CheckResult)
        .filter(CheckResult.dataset_id == dataset_id)
        .order_by(CheckResult.checked_at.desc())
        .all()
    )
    return results
