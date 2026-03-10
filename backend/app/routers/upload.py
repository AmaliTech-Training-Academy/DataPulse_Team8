"""Dataset upload router - IMPLEMENTED."""

import os, json, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.dataset import Dataset, DatasetFile
from app.models.user import User
from app.schemas.dataset import DatasetResponse, DatasetList
from app.services.file_parser import parse_csv, parse_json
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.post("/upload", response_model=DatasetResponse, status_code=201)
def upload_dataset(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a CSV or JSON file and store dataset metadata."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("csv", "json"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    content = file.file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    with open(file_path, "wb") as fh:
        fh.write(content)

    try:
        metadata = parse_csv(file_path) if ext == "csv" else parse_json(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse: {e}")

    dataset = Dataset(
        name=filename.rsplit(".", 1)[0],
        file_type=ext,
        row_count=metadata["row_count"],
        column_count=metadata["column_count"],
        column_names=json.dumps(metadata["column_names"]),
        status="PENDING",
        uploaded_by=current_user.id
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    df = DatasetFile(
        dataset_id=dataset.id, file_path=file_path, original_filename=filename
    )
    db.add(df)
    db.commit()
    return dataset


@router.get("", response_model=DatasetList)
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all datasets with pagination."""
    query = db.query(Dataset)
    if not current_user.is_admin:
        query = query.filter(Dataset.uploaded_by == current_user.id)
        
    total = query.count()
    datasets = query.offset(skip).limit(limit).all()
    return DatasetList(datasets=datasets, total=total)