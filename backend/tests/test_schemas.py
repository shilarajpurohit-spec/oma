"""
Tests for backend.schemas (Module 14)
"""

import pytest
from pydantic import ValidationError

from backend.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MigrationIssue,
    MigrationRequest,
    MigrationResponse,
    OdooVersion,
    Severity,
)


# ── Enum Tests ────────────────────────────────────────────────────
class TestOdooVersion:
    def test_all_versions_exist(self):
        assert OdooVersion.V15 == "15.0"
        assert OdooVersion.V16 == "16.0"
        assert OdooVersion.V17 == "17.0"
        assert OdooVersion.V18 == "18.0"
        assert OdooVersion.V19 == "19.0"

    def test_version_count(self):
        assert len(OdooVersion) == 5


class TestSeverity:
    def test_all_levels_exist(self):
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.HIGH == "high"
        assert Severity.CRITICAL == "critical"


# ── MigrationRequest Tests ───────────────────────────────────────
class TestMigrationRequest:
    def test_valid_request(self):
        req = MigrationRequest(
            module_name="sale_custom",
            source_version=OdooVersion.V15,
            file_content="class SaleOrder(models.Model): pass",
            filename="models/sale.py",
        )
        assert req.module_name == "sale_custom"
        assert req.source_version == OdooVersion.V15

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            MigrationRequest(
                module_name="sale_custom",
                # missing source_version, file_content, filename
            )

    def test_invalid_version(self):
        with pytest.raises(ValidationError):
            MigrationRequest(
                module_name="test",
                source_version="14.0",  # not supported
                file_content="code",
                filename="test.py",
            )


# ── MigrationIssue Tests ─────────────────────────────────────────
class TestMigrationIssue:
    def test_default_severity(self):
        issue = MigrationIssue(message="Deprecated API call")
        assert issue.severity == Severity.MEDIUM
        assert issue.line is None
        assert issue.suggestion == ""

    def test_full_issue(self):
        issue = MigrationIssue(
            line=42,
            severity=Severity.CRITICAL,
            message="fields.Many2many API changed",
            suggestion="Use Command.set() instead of [(6, 0, ids)]",
        )
        assert issue.line == 42
        assert issue.severity == Severity.CRITICAL


# ── MigrationResponse Tests ──────────────────────────────────────
class TestMigrationResponse:
    def test_minimal_response(self):
        resp = MigrationResponse(
            module_name="sale_custom",
            source_version="15.0",
            target_version="19.0",
            original_code="old code",
            migrated_code="new code",
        )
        assert resp.target_version == "19.0"
        assert resp.issues == []
        assert resp.diff == ""

    def test_response_with_issues(self):
        resp = MigrationResponse(
            module_name="test",
            source_version="16.0",
            target_version="19.0",
            original_code="old",
            migrated_code="new",
            issues=[
                MigrationIssue(message="Test issue"),
            ],
        )
        assert len(resp.issues) == 1


# ── ChatRequest Tests ────────────────────────────────────────────
class TestChatRequest:
    def test_valid_message(self):
        req = ChatRequest(message="How do I migrate many2many fields?")
        assert req.context is None

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_with_context(self):
        req = ChatRequest(message="Explain this", context="class Foo: pass")
        assert req.context == "class Foo: pass"


# ── ChatResponse Tests ───────────────────────────────────────────
class TestChatResponse:
    def test_defaults(self):
        resp = ChatResponse(reply="Here is the answer")
        assert resp.tokens_used == 0


# ── HealthResponse Tests ─────────────────────────────────────────
class TestHealthResponse:
    def test_health(self):
        resp = HealthResponse(version="0.1.0")
        assert resp.status == "ok"
