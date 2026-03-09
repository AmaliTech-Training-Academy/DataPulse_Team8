"""Scoring service - FULLY IMPLEMENTED."""


def calculate_quality_score(results: list, rules: list) -> dict:
    """Calculate weighted quality score (0-100).

    Weighting by severity:
        HIGH   = 3x weight
        MEDIUM = 2x weight
        LOW    = 1x weight

    Score = (sum of weights for passing rules / total weight) * 100
    """
    if not rules or not results:
        return {"score": 100.0, "total_rules": 0, "passed_rules": 0, "failed_rules": 0}

    severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    # Map rule_id -> rule object for quick lookup
    rule_map = {rule.id: rule for rule in rules}

    total_weight = 0
    passed_weight = 0
    passed_rules = 0
    failed_rules = 0

    for result in results:
        rule = rule_map.get(result.get("rule_id"))
        if rule is None:
            continue
        weight = severity_weights.get(rule.severity, 1)
        total_weight += weight
        if result.get("passed"):
            passed_weight += weight
            passed_rules += 1
        else:
            failed_rules += 1

    score = round((passed_weight / total_weight) * 100, 2) if total_weight > 0 else 100.0

    return {
        "score": score,
        "total_rules": len(rules),
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
    }
