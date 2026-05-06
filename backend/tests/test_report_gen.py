"""
Tests for backend.report_gen (Module 12)
"""

import json
from backend.schemas import MigrationResponse, MigrationIssue, Severity
from backend.report_gen import generate_report


def test_generate_report_json():
    resp = MigrationResponse(
        module_name="sale",
        source_version="15.0",
        target_version="19.0",
        original_code="old",
        migrated_code="new",
        explanation="test explain"
    )
    
    out = generate_report(resp, format="json")
    parsed = json.loads(out)
    assert parsed["module_name"] == "sale"
    assert parsed["source_version"] == "15.0"


def test_generate_report_text():
    resp = MigrationResponse(
        module_name="sale",
        source_version="15.0",
        target_version="19.0",
        original_code="old",
        migrated_code="new",
        explanation="test explain",
        issues=[
            MigrationIssue(line=10, severity=Severity.HIGH, message="Bad import", suggestion="Fix it")
        ],
        diff="--- a\n+++ b\n-old\n+new"
    )
    
    out = generate_report(resp, format="text")
    
    assert "OMA Agent Migration Report" in out
    assert "Module: sale" in out
    assert "test explain" in out
    assert "[HIGH] Line 10: Bad import" in out
    assert "Fix it" in out
    assert "+new" in out
