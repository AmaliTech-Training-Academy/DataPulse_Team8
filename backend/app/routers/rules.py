"""Validation rules router."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rule import ValidationRule
from app.models.user import User
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate
from app.utils.dependencies import get_current_user

router = APIRouter()

VALID_TYPES = {"NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}
VALID_DATA_TYPES = {"int", "float", "str", "bool"}


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new validation rule with comprehensive validation and RBAC."""
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
    
    try:
        rule = ValidationRule(**rule_data.model_dump(), created_by=current_user.id)
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")


@router.get("", response_model=list[RuleResponse])
def list_rules(
    dataset_type: Optional[str] = Query(None), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List validation rules - IMPLEMENTED."""
    q = db.query(ValidationRule).filter(ValidationRule.is_active)
    
    if not current_user.is_admin:
        q = q.filter(ValidationRule.created_by == current_user.id)
        
    if dataset_type:
        q = q.filter(ValidationRule.dataset_type == dataset_type)
    return q.all()


@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Permission check: Object owner or Admin
    if rule.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this rule"
        )

    update_data = rule_data.model_dump(exclude_unset=True)

    # Validation checks for changed fields
    if "rule_type" in update_data and update_data["rule_type"] not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid rule_type: {VALID_TYPES}")
    if "severity" in update_data and update_data["severity"] not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=400, detail=f"Invalid severity: {VALID_SEVERITIES}"
        )

    try:
        for key, value in update_data.items():
            setattr(rule, key, value)
        db.commit()
        db.refresh(rule)
        return rule
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error during update: {str(e)}"
        )


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
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Permission check: Object owner or Admin
    if rule.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this rule"
        )

    try:
        rule.is_active = False
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error during delete: {str(e)}"
        )

    return None