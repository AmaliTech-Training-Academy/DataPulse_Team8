"""Dataset upload router - IMPLEMENTED."""

import os, json, uuid
import pandas as pd
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

# File size limit: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


@router.post("/upload", response_model=DatasetResponse, status_code=201)
def upload_dataset(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a CSV or JSON file and store dataset metadata.
    
    Validations:
    - File type must be .csv or .json
    - File size must not exceed 10MB
    - File must not be empty
    - File must be parseable by pandas
    """
    filename = file.filename or ""
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required. Please provide a valid file."
        )
    
    # Validate file extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("csv", "json"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Only CSV and JSON files are supported."
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    # Read file content
    content = file.file.read()
    
    # Validate file is not empty
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty. Please provide a file with data."
        )
    
    # Validate file size (10MB max)
    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File size ({size_mb:.2f}MB) exceeds maximum allowed size of 10MB."
        )
    
    # Write file to disk
    with open(file_path, "wb") as fh:
        fh.write(content)

    # Parse file and extract metadata
    try:
        metadata = parse_csv(file_path) if ext == "csv" else parse_json(file_path)
    except pd.errors.EmptyDataError:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail="File contains no data. Please upload a file with at least one row."
        )
    except pd.errors.ParserError as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse {ext.upper()} file. The file may be malformed: {str(e)}"
        )
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {ext.upper()} format: {str(e)}"
        )
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Unexpected error while parsing file: {str(e)}"
        )

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