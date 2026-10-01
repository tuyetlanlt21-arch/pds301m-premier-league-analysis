from scripts.ai_review.rule_loader import contract_fields, load_rules, repository_root


def test_loads_canonical_documentation() -> None:
    rules = load_rules(repository_root())
    assert "Raw data is immutable" in rules["docs/PROJECT_RULES.md"]
    assert {"Season", "FTHG", "FTR"}.issubset(contract_fields(rules))
