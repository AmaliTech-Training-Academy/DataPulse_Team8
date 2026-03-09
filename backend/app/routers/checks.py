"""Quality checks router - FULLY IMPLEMENTED."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.dataset import Dataset, DatasetFile
from app.models.rule import ValidationRule
from app.models.check_result import CheckResult, QualityScore
from app.schemas.report import CheckResultResponse
from app.services.file_parser import parse_csv, parse_json
from app.services.validation_engine import ValidationEngine
from app.services.scoring_service import calculate_quality_score

router = APIRouter()


@router.post("/run/{dataset_id}", status_code=200)
def run_checks(dataset_id: int, db: Session = Depends(get_db)):
    """Run all applicable validation checks on a dataset."""

    # 1. Fetch dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    # 2. Get the file path
    dataset_file = (
        db.query(DatasetFile)
        .filter(DatasetFile.dataset_id == dataset_id)
        .first()
    )
    if not dataset_file:
        raise HTTPException(status_code=404, detail="No file found for this dataset")

    # 3. Parse the file into a DataFrame
    try:
        if dataset.file_type == "csv":
            parsed = parse_csv(dataset_file.file_path)
        else:
            parsed = parse_json(dataset_file.file_path)
        df = parsed["dataframe"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read dataset file: {e}")

    # 4. Fetch active rules matching this dataset's file type
    rules = (
        db.query(ValidationRule)
        .filter(
            ValidationRule.is_active == True,
            ValidationRule.dataset_type == dataset.file_type,
        )
        .all()
    )

    # 5. Run all checks
    engine = ValidationEngine()
    check_results = engine.run_all_checks(df, rules)

    # 6. Persist CheckResult records
    for res in check_results:
        record = CheckResult(
            dataset_id=dataset_id,
            rule_id=res["rule_id"],
            passed=res["passed"],
            failed_rows=res["failed_rows"],
            total_rows=res["total_rows"],
            details=res.get("details", ""),
        )
        db.add(record)

    # 7. Calculate quality score
    score_data = calculate_quality_score(check_results, rules)

    # 8. Persist QualityScore record
    quality_score = QualityScore(
        dataset_id=dataset_id,
        score=score_data["score"],
        total_rules=score_data["total_rules"],
        passed_rules=score_data["passed_rules"],
        failed_rules=score_data["failed_rules"],
    )
    db.add(quality_score)

    # 9. Update dataset status
    dataset.status = "VALIDATED" if score_data["score"] >= 50.0 else "FAILED"
    db.commit()

    # 10. Return summary
    return {
        "dataset_id": dataset_id,
        "score": score_data["score"],
        "total_rules": score_data["total_rules"],
        "passed_rules": score_data["passed_rules"],
        "failed_rules": score_data["failed_rules"],
        "status": dataset.status,
        "results_count": len(check_results),
    }


@router.get("/results/{dataset_id}", response_model=list[CheckResultResponse])
def get_check_results(dataset_id: int, db: Session = Depends(get_db)):
    """Get all check results for a dataset, ordered most recent first."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    results = (
        db.query(CheckResult)
        .filter(CheckResult.dataset_id == dataset_id)
        .order_by(CheckResult.checked_at.desc())
        .all()
    )
    return results
