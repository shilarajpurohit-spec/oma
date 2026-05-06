"""
OMA Agent — API Schemas (Module 14)
Pydantic models for request / response validation.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ── Enums ─────────────────────────────────────────────────────────
class OdooVersion(str, Enum):
    """Supported Odoo versions (source and target)."""
    V15 = "15.0"
    V16 = "16.0"
    V17 = "17.0"
    V18 = "18.0"
    V19 = "19.0"

    @classmethod
    def newer_than(cls, version: "OdooVersion") -> list["OdooVersion"]:
        """Return all versions strictly newer than the given version."""
        order = list(cls)
        idx = order.index(version)
        return order[idx + 1:]


class Severity(str, Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Migration ────────────────────────────────────────────────────
class MigrationRequest(BaseModel):
    """Payload sent by the client to start a migration."""
    module_name: str = Field(..., description="Technical name of the Odoo module")
    source_version: OdooVersion = Field(..., description="Current Odoo version")
    target_version: OdooVersion = Field(OdooVersion.V19, description="Target Odoo version to migrate to")
    file_content: str = Field(..., description="Raw source code to migrate")
    filename: str = Field(..., description="Original filename (e.g. models/sale.py)")
    incremental: bool = Field(False, description="If True, migrate step-by-step through intermediate versions")

    @model_validator(mode="after")
    def validate_versions(self) -> "MigrationRequest":
        src_order = list(OdooVersion)
        if src_order.index(self.source_version) >= src_order.index(self.target_version):
            raise ValueError(
                f"target_version ({self.target_version}) must be newer than "
                f"source_version ({self.source_version})"
            )
        return self


class FileItem(BaseModel):
    """A single file in a multi-file migration batch."""
    filename: str = Field(..., description="Filename relative to module root")
    content: str = Field(..., description="Raw file content")


class MultiFileMigrationRequest(BaseModel):
    """Payload for migrating an entire module (multiple files) at once."""
    module_name: str = Field(..., description="Technical name of the Odoo module")
    source_version: OdooVersion = Field(..., description="Current Odoo version")
    target_version: OdooVersion = Field(OdooVersion.V19, description="Target Odoo version")
    files: list[FileItem] = Field(..., min_length=1, description="List of files to migrate")
    incremental: bool = Field(False, description="Step-by-step migration through intermediate versions")


class MigrationIssue(BaseModel):
    """A single issue detected during migration."""
    line: Optional[int] = None
    severity: Severity = Severity.MEDIUM
    message: str
    suggestion: str = ""


class MigrationResponse(BaseModel):
    """Result returned after a migration run."""
    module_name: str
    source_version: str
    target_version: str
    original_code: str
    migrated_code: str
    diff: str = ""
    issues: list[MigrationIssue] = []
    explanation: str = ""
    filename: str = ""
    incremental_steps: list[dict] = []   # populated when incremental=True


class MultiFileMigrationResult(BaseModel):
    """Result for a single file within a multi-file migration."""
    filename: str
    response: MigrationResponse


class MultiFileMigrationResponse(BaseModel):
    """Aggregated result from migrating an entire module."""
    module_name: str
    source_version: str
    target_version: str
    results: list[MultiFileMigrationResult] = []
    total_issues: int = 0
    skipped_files: list[str] = []


# ── Chat ─────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """User message sent to the agent chat."""
    message: str = Field(..., min_length=1)
    context: Optional[str] = Field(None, description="Optional code context")


class ChatResponse(BaseModel):
    """Agent reply from the chat endpoint."""
    reply: str
    tokens_used: int = 0


# ── Health ───────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    version: str


# ── Reports ──────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    """Payload to generate a migration report."""
    response: MigrationResponse = Field(..., description="The result from a migration run")
    format: str = Field("json", description="Report format: 'json' or 'text'")


# ── Version Detection ────────────────────────────────────────────
class VersionDetectRequest(BaseModel):
    """Payload to detect Odoo version from source code."""
    code: str
    filename: str

class VersionDetectResponse(BaseModel):
    """Result of version detection."""
    version: str


# ── Apply Fix ─────────────────────────────────────────────────────
class ApplyFixRequest(BaseModel):
    """Payload to apply a single targeted fix to source code via LLM."""
    code: str = Field(..., description="Current source code")
    issue_message: str = Field(..., description="The issue description")
    suggestion: str = Field(..., description="The fix suggestion/hint")
    line: Optional[int] = Field(None, description="Line number where the issue was detected")


class ApplyFixResponse(BaseModel):
    """Result after applying a fix."""
    patched_code: str = Field(..., description="The updated source code")
    applied: bool = Field(True, description="Whether the fix was successfully applied")
    message: str = Field("", description="Optional status message")
