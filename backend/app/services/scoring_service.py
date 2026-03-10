"""Scoring service - IMPLEMENTED."""


def calculate_quality_score(results: list, rules: list) -> dict:
    """Calculate weighted quality score.

    Weighting by severity:
        HIGH = 3x weight
        MEDIUM = 2x weight
        LOW = 1x weight

    Steps:
    1. Map each result to its corresponding rule
    2. Calculate weighted pass/fail for each check
    3. Compute overall score as weighted average (0-100)
    4. Return dict with score, total_rules, passed_rules, failed_rules
    """
    severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    rule_map = {rule.id: rule for rule in rules}
    total_weight = 0
    earned_weight = 0
    passed_rules = 0
    failed_rules = 0

    for res in results:
        rule = rule_map.get(res["rule_id"])
        if not rule:
            continue

        weight = severity_weights.get(rule.severity.upper(), 2)
        total_weight += weight

        if res["passed"]:
            earned_weight += weight
            passed_rules += 1
        else:
            failed_rules += 1

    score = (earned_weight / total_weight) * 100 if total_weight > 0 else 0.0

    return {
        "score": round(score, 2),
        "total_rules": len(rules),
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
    }
