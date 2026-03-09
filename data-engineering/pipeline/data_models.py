"""SQLAlchemy ORM for analytics tables."""

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey
from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import declarative_base

AnalyticsBase = declarative_base()


class EtlBatchRun(AnalyticsBase):
    __tablename__ = "etl_batch_runs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pipeline_name = Column(String(100), nullable=False, default="analytics_etl")
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False)
    source_watermark = Column(DateTime(timezone=True))
    target_watermark = Column(DateTime(timezone=True))
    rows_extracted = Column(Integer, nullable=False, default=0)
    rows_loaded = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)


class DimDataset(AnalyticsBase):
    __tablename__ = "dim_datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)
    column_names = Column(Text)
    uploaded_by = Column(Integer)
    uploaded_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)


class DimRule(AnalyticsBase):
    __tablename__ = "dim_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    dataset_type = Column(String(100), nullable=False)
    field_name = Column(String(255), nullable=False)
    rule_type = Column(String(20), nullable=False)
    parameters = Column(Text)
    severity = Column(String(10), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False)
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)


class DimDate(AnalyticsBase):
    __tablename__ = "dim_date"
    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date, nullable=False, unique=True)
    day_of_week = Column(Integer, nullable=False)
    day_of_month = Column(Integer, nullable=False)
    day_of_year = Column(Integer, nullable=False)
    week_of_year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(12), nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)


class FactQualityCheck(AnalyticsBase):
    __tablename__ = "fact_quality_checks"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_check_result_id = Column(Integer, nullable=False, unique=True)
    dataset_id = Column(Integer, ForeignKey("dim_datasets.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("dim_rules.id"), nullable=False)
    rule_type = Column(String(20), nullable=False)
    severity = Column(String(10), nullable=False)
    passed = Column(Boolean, nullable=False)
    failed_rows = Column(Integer, nullable=False, default=0)
    total_rows = Column(Integer, nullable=False, default=0)
    failure_rate = Column(Numeric(7, 4), nullable=False, default=0)
    score = Column(Numeric(5, 2))
    details = Column(Text)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    etl_batch_id = Column(BigInteger, ForeignKey("etl_batch_runs.id"))
    etl_loaded_at = Column(DateTime(timezone=True), nullable=False)


class FactQualityScore(AnalyticsBase):
    __tablename__ = "fact_quality_scores"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_quality_score_id = Column(Integer, nullable=False, unique=True)
    dataset_id = Column(Integer, ForeignKey("dim_datasets.id"), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    total_rules = Column(Integer, nullable=False, default=0)
    passed_rules = Column(Integer, nullable=False, default=0)
    failed_rules = Column(Integer, nullable=False, default=0)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    etl_batch_id = Column(BigInteger, ForeignKey("etl_batch_runs.id"))
    etl_loaded_at = Column(DateTime(timezone=True), nullable=False)
