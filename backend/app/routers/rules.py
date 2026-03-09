"""Validation rules router - FULLY IMPLEMENTED."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rule import ValidationRule
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()

VALID_TYPES      = {"NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(rule_data: RuleCreate, db: Session = Depends(get_db)):
    """Create a new validation rule."""
    if rule_data.rule_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid rule_type. Must be one of: {VALID_TYPES}")
    if rule_data.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {VALID_SEVERITIES}")
    rule = ValidationRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=list[RuleResponse])
def list_rules(dataset_type: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """List all active validation rules, optionally filtered by dataset_type."""
    q = db.query(ValidationRule).filter(ValidationRule.is_active == True)
    if dataset_type:
        q = q.filter(ValidationRule.dataset_type == dataset_type)
    return q.all()


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, rule_data: RuleUpdate, db: Session = Depends(get_db)):
    """Update an existing validation rule (partial update supported)."""
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    update_data = rule_data.model_dump(exclude_none=True)

    if "rule_type" in update_data and update_data["rule_type"] not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid rule_type. Must be one of: {VALID_TYPES}")
    if "severity" in update_data and update_data["severity"] not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {VALID_SEVERITIES}")

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Soft-delete a validation rule (sets is_active=False)."""
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    rule.is_active = False
    db.commit()
    return Response(status_code=204)
