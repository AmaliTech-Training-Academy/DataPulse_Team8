"""test_scoring.py — Unit tests for calculate_quality_score (fully implemented)."""
import pytest
from unittest.mock import MagicMock
from app.services.scoring_service import calculate_quality_score


def make_rule(rule_id, severity="HIGH"):
    r = MagicMock(); r.id = rule_id; r.severity = severity; return r

def make_result(rule_id, passed):
    return {"rule_id": rule_id, "passed": passed, "failed_rows": 0, "total_rows": 10}


class TestScoringService:
    def test_all_pass_score_100(self):
        rules = [make_rule(1, "HIGH"), make_rule(2, "MEDIUM"), make_rule(3, "LOW")]
        results = [make_result(1, True), make_result(2, True), make_result(3, True)]
        out = calculate_quality_score(results, rules)
        assert out["score"] == 100.0 and out["passed_rules"] == 3 and out["failed_rules"] == 0

    def test_all_fail_score_0(self):
        rules = [make_rule(1, "HIGH"), make_rule(2, "MEDIUM"), make_rule(3, "LOW")]
        results = [make_result(1, False), make_result(2, False), make_result(3, False)]
        out = calculate_quality_score(results, rules)
        assert out["score"] == 0.0 and out["passed_rules"] == 0

    def test_high_fails_weighted_50(self):
        # HIGH(3)+MEDIUM(2)+LOW(1)=6 total. HIGH fails → passed=3 → 50.0
        rules = [make_rule(1, "HIGH"), make_rule(2, "MEDIUM"), make_rule(3, "LOW")]
        results = [make_result(1, False), make_result(2, True), make_result(3, True)]
        out = calculate_quality_score(results, rules)
        assert out["score"] == pytest.approx(50.0, rel=1e-2)

    def test_only_low_rules_all_pass(self):
        rules = [make_rule(i, "LOW") for i in range(1, 4)]
        results = [make_result(i, True) for i in range(1, 4)]
        assert calculate_quality_score(results, rules)["score"] == 100.0

    def test_score_always_in_range(self):
        rules = [make_rule(1, "HIGH"), make_rule(2, "MEDIUM")]
        results = [make_result(1, True), make_result(2, False)]
        out = calculate_quality_score(results, rules)
        assert 0.0 <= out["score"] <= 100.0

    def test_counts_consistent(self):
        rules = [make_rule(i, "MEDIUM") for i in range(1, 6)]
        results = [make_result(i, i % 2 == 0) for i in range(1, 6)]
        out = calculate_quality_score(results, rules)
        assert out["passed_rules"] + out["failed_rules"] == out["total_rules"]

    def test_empty_returns_safe_defaults(self):
        out = calculate_quality_score([], [])
        assert isinstance(out["score"], float) and 0.0 <= out["score"] <= 100.0
