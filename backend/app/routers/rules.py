"""Validation rules router - FULLY IMPLEMENTED."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rule import ValidationRule
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()

VALID_TYPES      = {"NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}
VALID_DATA_TYPES = {"int", "float", "str", "bool"}


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(rule_data: RuleCreate, db: Session = Depends(get_db)):
    """Create a new validation rule with comprehensive validation."""
    # Validate rule type
    if rule_data.rule_type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule_type '{rule_data.rule_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}"
        )
    
    # Validate severity
    if rule_data.severity not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity '{rule_data.severity}'. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}"
        )
    
    # Validate field name is not empty
    if not rule_data.field_name or not rule_data.field_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Field name cannot be empty"
        )
    
    # Validate parameters based on rule type
    _validate_rule_parameters(rule_data.rule_type, rule_data.parameters)
    
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


def _validate_rule_parameters(rule_type: str, parameters: Optional[str]) -> None:
    """Validate rule parameters based on rule type.
    
    Args:
        rule_type: The type of validation rule
        parameters: JSON string of parameters
        
    Raises:
        HTTPException: If parameters are invalid for the rule type
    """
    if rule_type in ["DATA_TYPE", "RANGE", "REGEX"]:
        if not parameters:
            raise HTTPException(
                status_code=400,
                detail=f"Rule type '{rule_type}' requires parameters"
            )
        
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Parameters must be valid JSON"
            )
        
        # Validate DATA_TYPE parameters
        if rule_type == "DATA_TYPE":
            if "expected_type" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="DATA_TYPE rule requires 'expected_type' parameter"
                )
            if params["expected_type"] not in VALID_DATA_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid expected_type '{params['expected_type']}'. Must be one of: {', '.join(sorted(VALID_DATA_TYPES))}"
                )
        
        # Validate RANGE parameters
        elif rule_type == "RANGE":
            if "min" not in params and "max" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="RANGE rule requires at least 'min' or 'max' parameter"
                )
            if "min" in params and "max" in params:
                if params["min"] >= params["max"]:
                    raise HTTPException(
                        status_code=400,
                        detail="RANGE rule: 'min' must be less than 'max'"
                    )
        
        # Validate REGEX parameters
        elif rule_type == "REGEX":
            if "pattern" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="REGEX rule requires 'pattern' parameter"
                )
            if not params["pattern"]:
                raise HTTPException(
                    status_code=400,
                    detail="REGEX pattern cannot be empty"
                )


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Soft-delete a validation rule (sets is_active=False)."""
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    rule.is_active = False
    db.commit()
    return Response(status_code=204)
