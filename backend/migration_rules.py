"""
OMA Agent — Migration Rules (Module 06)
Rule definitions for Odoo version-to-version migration.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.schemas import OdooVersion, Severity


@dataclass
class MigrationRule:
    """A single migration rule."""

    id: str
    pattern: str  # regex pattern to search for
    replacement: str  # replacement string (may use regex groups)
    description: str
    source_versions: list[OdooVersion]  # versions this rule applies FROM
    severity: Severity = Severity.MEDIUM
    category: str = "general"


# ── Rule definitions ──────────────────────────────────────────────

_RULES: list[MigrationRule] = [
    # ── Deprecated API changes ────────────────────────────────────
    MigrationRule(
        id="dep-001",
        pattern=r"from openerp import",
        replacement="from odoo import",
        description="Replace legacy 'openerp' imports with 'odoo'.",
        source_versions=[OdooVersion.V15],
        severity=Severity.HIGH,
        category="imports",
    ),
    MigrationRule(
        id="dep-002",
        pattern=r"from openerp\.addons",
        replacement="from odoo.addons",
        description="Replace legacy 'openerp.addons' imports.",
        source_versions=[OdooVersion.V15],
        severity=Severity.HIGH,
        category="imports",
    ),

    # ── Field changes ─────────────────────────────────────────────
    MigrationRule(
        id="fld-001",
        pattern=r"fields\.Char\(([^)]*?)string=",
        replacement=r"fields.Char(\1string=",
        description="Char field — verify positional 'string' is keyword.",
        source_versions=[OdooVersion.V15, OdooVersion.V16],
        severity=Severity.LOW,
        category="fields",
    ),
    MigrationRule(
        id="fld-002",
        pattern=r"fields\.Selection\(\s*selection=",
        replacement="fields.Selection(",
        description="Selection field — 'selection' is now positional in v19.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.MEDIUM,
        category="fields",
    ),

    # ── OWL migration (JS-related but detected in Python context) ─
    MigrationRule(
        id="owl-001",
        pattern=r"owl\.Component",
        replacement="Component",
        description="OWL1 → OWL2: `owl.Component` is now just `Component`.",
        source_versions=[OdooVersion.V15, OdooVersion.V16],
        severity=Severity.HIGH,
        category="owl",
    ),

    # ── Controller / HTTP ─────────────────────────────────────────
    MigrationRule(
        id="http-001",
        pattern=r"@http\.route\(",
        replacement="@http.route(",
        description="Verify http.route decorator — auth and methods params may need updating.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17],
        severity=Severity.MEDIUM,
        category="controllers",
    ),
    MigrationRule(
        id="http-002",
        pattern=r"type=['\"]json['\"]",
        replacement="type='json'",
        description="JSON controller type — verify compatibility with v19 JSON-RPC changes.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.MEDIUM,
        category="controllers",
    ),

    # ── Manifest ──────────────────────────────────────────────────
    MigrationRule(
        id="mfst-001",
        pattern=r"['\"]version['\"]\s*:\s*['\"](\d+)\.0\.",
        replacement="'version': '19.0.",
        description="Update module version to 19.0 in __manifest__.py.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.HIGH,
        category="manifest",
    ),

    # ── Deprecated methods ────────────────────────────────────────
    MigrationRule(
        id="meth-001",
        pattern=r"\.sudo\(\s*\w+\s*\)",
        replacement=".sudo()",
        description="sudo() no longer accepts a user argument in v19 — use with_user() instead.",
        source_versions=[OdooVersion.V15, OdooVersion.V16],
        severity=Severity.HIGH,
        category="methods",
    ),
    MigrationRule(
        id="meth-002",
        pattern=r"\.search_read\(",
        replacement=".search_read(",
        description="Verify search_read() — domain and fields params order may differ.",
        source_versions=[OdooVersion.V15],
        severity=Severity.LOW,
        category="methods",
    ),
    MigrationRule(
        id="meth-003",
        pattern=r"self\.pool\[",
        replacement="self.env[",
        description="Replace deprecated self.pool[] with self.env[].",
        source_versions=[OdooVersion.V15],
        severity=Severity.CRITICAL,
        category="methods",
    ),

    # ── Web assets ────────────────────────────────────────────────
    MigrationRule(
        id="asset-001",
        pattern=r"['\"]web\.assets_backend['\"]",
        replacement="'web.assets_backend'",
        description="Verify web.assets_backend bundle structure — v17+ uses new asset format.",
        source_versions=[OdooVersion.V15, OdooVersion.V16],
        severity=Severity.MEDIUM,
        category="assets",
    ),

    # ── XML / View changes ────────────────────────────────────────
    MigrationRule(
        id="xml-001",
        pattern=r'<field name="view_type">form</field>',
        replacement="",
        description="Remove deprecated view_type='form' in action definitions.",
        source_versions=[OdooVersion.V15],
        severity=Severity.MEDIUM,
        category="xml",
    ),
]


def get_rules(source_version: OdooVersion) -> list[MigrationRule]:
    """Get all migration rules applicable to a given source version.

    Args:
        source_version: The Odoo version being migrated FROM.

    Returns:
        List of applicable MigrationRule objects.
    """
    return [r for r in _RULES if source_version in r.source_versions]


def get_all_rules() -> list[MigrationRule]:
    """Return every registered migration rule."""
    return list(_RULES)
