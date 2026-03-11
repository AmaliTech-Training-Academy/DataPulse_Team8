from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    dataset_type = Column(String(100), nullable=False)
    field_name = Column(String(255), nullable=False)
    rule_type = Column(String(20), nullable=False)
    parameters = Column(Text, nullable=True)
    severity = Column(String(10), default="MEDIUM")
    is_active = Column(Boolean, default=True)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
