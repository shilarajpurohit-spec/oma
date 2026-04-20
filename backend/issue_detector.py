"""
OMA Agent — Issue Detector (Module 08)
Detect migration issues with severity and fix hints.
"""

from __future__ import annotations

import re

from backend.code_analyzer import AnalysisResult
from backend.schemas import MigrationIssue, OdooVersion, Severity


# ── Issue checks ──────────────────────────────────────────────────

_ISSUE_CHECKS: list[dict] = [
    # ── Deprecated patterns ───────────────────────────────────────
    {
        "pattern": re.compile(r"from openerp\b"),
        "versions": [OdooVersion.V15],
        "severity": Severity.CRITICAL,
        "message": "Uses deprecated 'openerp' import — must change to 'odoo'.",
        "suggestion": "Replace `from openerp` with `from odoo`.",
    },
    {
        "pattern": re.compile(r"self\.pool\["),
        "versions": [OdooVersion.V15],
        "severity": Severity.CRITICAL,
        "message": "Uses deprecated `self.pool[]` registry access.",
        "suggestion": "Replace `self.pool['model.name']` with `self.env['model.name']`.",
    },
    {
        "pattern": re.compile(r"\.sudo\(\s*\w+\s*\)"),
        "versions": [OdooVersion.V15, OdooVersion.V16],
        "severity": Severity.HIGH,
        "message": "`sudo(user)` is no longer supported — use `with_user(user).sudo()`.",
        "suggestion": "Replace `.sudo(user)` with `.with_user(user).sudo()`.",
    },
    {
        "pattern": re.compile(r"osv\.osv\b|osv\.Model\b"),
        "versions": [OdooVersion.V15],
        "severity": Severity.CRITICAL,
        "message": "Uses removed `osv.osv` / `osv.Model` base class.",
        "suggestion": "Inherit from `models.Model` instead.",
    },
    {
        "pattern": re.compile(r"fields_get_keys|fields_get\b"),
        "versions": [OdooVersion.V15, OdooVersion.V16],
        "severity": Severity.MEDIUM,
        "message": "Uses `fields_get` / `fields_get_keys` — API may have changed.",
        "suggestion": "Review the v19 ORM API docs for updated method signatures.",
    },

    # ── OWL / JS concerns ────────────────────────────────────────
    {
        "pattern": re.compile(r"owl\.Component|owl\.tags"),
        "versions": [OdooVersion.V15, OdooVersion.V16],
        "severity": Severity.HIGH,
        "message": "Uses OWL1 JavaScript patterns — v17+ requires OWL2.",
        "suggestion": "Rewrite OWL components using OWL2 Component class and setup() lifecycle.",
    },

    # ── Manifest version ─────────────────────────────────────────
    {
        "pattern": re.compile(r"""['"]version['"]\s*:\s*['"](?:15|16|17|18)\.0"""),
        "versions": [OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        "severity": Severity.HIGH,
        "message": "Module manifest version is not 19.0 — must be updated.",
        "suggestion": "Change the version field to '19.0.x.x.x'.",
    },

    # ── Deprecated XML ────────────────────────────────────────────
    {
        "pattern": re.compile(r'<field name="view_type">'),
        "versions": [OdooVersion.V15],
        "severity": Severity.MEDIUM,
        "message": "`view_type` field in action XML is deprecated and removed.",
        "suggestion": "Remove the `<field name=\"view_type\">` element entirely.",
    },

    # ── web.assets changes ────────────────────────────────────────
    {
        "pattern": re.compile(r"qweb\s*:\s*\["),
        "versions": [OdooVersion.V15, OdooVersion.V16],
        "severity": Severity.MEDIUM,
        "message": "`qweb` key in __manifest__ is deprecated — use `assets` instead.",
        "suggestion": "Move QWeb templates to the `assets` key with proper bundle names.",
    },

    # ── Raw SQL ───────────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"\b(?:self\.env\.cr|self\._cr|(?<!\.)(cr))\s*\.\s*execute\s*\("
        ),
        "versions": [OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        "severity": Severity.HIGH,
        "message": "Uses raw SQL via `cr.execute()` — table/column names may have changed in Odoo 19.",
        "suggestion": (
            "Prefer ORM methods where possible. If raw SQL is required, verify all "
            "table and column names against Odoo 19 ORM mappings and check for "
            "deprecated `ir.rule` or `ir.model.access` schema changes."
        ),
    },
    {
        "pattern": re.compile(
            r"(?:f?['\"])\s*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+",
            re.IGNORECASE,
        ),
        "versions": [OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        "severity": Severity.MEDIUM,
        "message": "Detected inline SQL string — verify query compatibility with Odoo 19 schema.",
        "suggestion": (
            "Check that all table names match Odoo 19 ORM `_table` declarations. "
            "Consider replacing with ORM calls (`search`, `read`, `write`) for safer migrations."
        ),
    },
]


def detect_issues(
    code: str,
    source_version: OdooVersion,
    analysis: AnalysisResult | None = None,
) -> list[MigrationIssue]:
    """Scan code for migration issues relevant to the given source version.

    Args:
        code: Raw source code.
        source_version: The Odoo version being migrated from.
        analysis: Optional pre-computed AnalysisResult (for future use).

    Returns:
        List of MigrationIssue objects.
    """
    issues: list[MigrationIssue] = []
    lines = code.splitlines()

    for check in _ISSUE_CHECKS:
        if source_version not in check["versions"]:
            continue

        for line_num, line_text in enumerate(lines, 1):
            if check["pattern"].search(line_text):
                issues.append(
                    MigrationIssue(
                        line=line_num,
                        severity=check["severity"],
                        message=check["message"],
                        suggestion=check["suggestion"],
                    )
                )

    return issues
