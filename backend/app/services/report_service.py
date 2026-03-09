"""Report service - STUB: Needs implementation."""


from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.check_result import CheckResult, QualityScore
from app.models.rule import ValidationRule

def generate_report(dataset_id: int, db: Session) -> dict:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return None

    latest_score = db.query(QualityScore).filter(
        QualityScore.dataset_id == dataset_id
    ).order_by(QualityScore.checked_at.desc()).first()

    if not latest_score:
        return None

    results = db.query(CheckResult).filter(
        CheckResult.dataset_id == dataset_id
    ).order_by(CheckResult.id.desc()).all()

    # Build recommendations and failure patterns
    failed_results = [r for r in results if not r.passed]
    failure_patterns = {}
    
    # fetch rules to know names
    rules = {r.id: r for r in db.query(ValidationRule).all()}

    for res in failed_results:
        rule_name = rules[res.rule_id].name if res.rule_id in rules else f"Rule {res.rule_id}"
        if rule_name not in failure_patterns:
            failure_patterns[rule_name] = {"rule_name": rule_name, "count": 0, "failed_rows": 0}
        failure_patterns[rule_name]["count"] += 1
        failure_patterns[rule_name]["failed_rows"] += res.failed_rows

    top_patterns = sorted(failure_patterns.values(), key=lambda x: x["failed_rows"], reverse=True)[:10]

    recommendations = []
    for pattern in top_patterns:
        recommendations.append(f"Review rows failing '{pattern['rule_name']}' which affected {pattern['failed_rows']} rows.")

    executive_summary = {
        "status": "Excellent" if latest_score.score >= 90 else "Good" if latest_score.score >= 70 else "Needs Improvement",
        "score_percentage": f"{latest_score.score:.1f}%",
        "passed_rules": latest_score.passed_rules,
        "failed_rules": latest_score.failed_rules,
    }

    report = {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "score": latest_score.score,
        "total_rules": latest_score.total_rules,
        "passed_rules": latest_score.passed_rules,
        "failed_rules": latest_score.failed_rules,
        "executive_summary": executive_summary,
        "top_failure_patterns": top_patterns,
        "recommendations": recommendations,
        "results": results,
        "checked_at": latest_score.checked_at
    }
    
    return report


def get_trend_data(dataset_id: Optional[int], start_date: datetime, end_date: datetime, interval: str, db: Session) -> dict:
    query = db.query(QualityScore).filter(
        QualityScore.checked_at >= start_date,
        QualityScore.checked_at <= end_date
    )

    if dataset_id:
        query = query.filter(QualityScore.dataset_id == dataset_id)

    scores_records = query.order_by(QualityScore.checked_at).all()
    
    # Group in Python to remain DB-agnostic (works on both SQLite and Postgres)
    grouped_data = {}
    
    for record in scores_records:
        if interval == "day":
            date_key = record.checked_at.strftime("%Y-%m-%d")
        elif interval == "week":
            # Monday of the week
            date_key = (record.checked_at - timedelta(days=record.checked_at.weekday())).strftime("%Y-%m-%d")
        else: # month
            date_key = record.checked_at.strftime("%Y-%m-01")
            
        if date_key not in grouped_data:
            grouped_data[date_key] = {"sum": 0.0, "count": 0}
            
        grouped_data[date_key]["sum"] += record.score
        grouped_data[date_key]["count"] += 1
        
    trend_datapoints = []
    scores = []
    
    for date_str in sorted(grouped_data.keys()):
        data = grouped_data[date_str]
        avg = data["sum"] / data["count"]
        
        trend_datapoints.append({
            "date": date_str,
            "average_score": float(avg),
            "check_count": data["count"]
        })
        scores.append(float(avg))
        
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    direction = "flat"
    if len(scores) > 1:
        start_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        end_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        if end_avg - start_avg > 2.0:
            direction = "up"
        elif start_avg - end_avg > 2.0:
            direction = "down"
            
    volatility = 0.0
    if len(scores) > 1:
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        volatility = variance ** 0.5
        
    return {
        "dataset_id": dataset_id,
        "trend_data": trend_datapoints,
        "average_score": round(avg_score, 2),
        "trend_direction": direction,
        "volatility": round(volatility, 2)
    }
