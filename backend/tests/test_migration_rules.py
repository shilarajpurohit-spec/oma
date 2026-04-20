"""
Tests for backend.migration_rules (Module 06)
"""

from backend.migration_rules import get_rules, get_all_rules, MigrationRule
from backend.schemas import OdooVersion, Severity


def test_get_all_rules():
    rules = get_all_rules()
    assert len(rules) > 5  # There should be at least a few rules defined
    assert all(isinstance(r, MigrationRule) for r in rules)


def test_get_rules_by_version():
    v15_rules = get_rules(OdooVersion.V15)
    v18_rules = get_rules(OdooVersion.V18)
    
    assert len(v15_rules) > len(v18_rules)  # v15 should have more deprecated stuff than v18
    
    # Verify specific v15-only rules
    openerp_rule = next((r for r in v15_rules if r.id == "dep-001"), None)
    assert openerp_rule is not None
    assert OdooVersion.V15 in openerp_rule.source_versions
    assert getattr(openerp_rule, "severity") == Severity.HIGH

    # Verify rule not in v18
    assert next((r for r in v18_rules if r.id == "dep-001"), None) is None


def test_rule_structure():
    rule = get_all_rules()[0]
    assert hasattr(rule, "id")
    assert hasattr(rule, "pattern")
    assert hasattr(rule, "replacement")
    assert hasattr(rule, "description")
    assert hasattr(rule, "source_versions")
    assert hasattr(rule, "severity")
    assert hasattr(rule, "category")
