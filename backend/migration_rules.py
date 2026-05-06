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
    min_target_version: OdooVersion | None = None  # rule only fires when target >= this


# ── Version order (for range comparisons) ─────────────────────────
_VERSION_ORDER = [OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18, OdooVersion.V19]


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
        description="Selection field — 'selection' is now positional.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.MEDIUM,
        category="fields",
    ),

    # ── OWL migration ─────────────────────────────────────────────
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
        description="JSON controller type — verify compatibility with JSON-RPC changes.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.MEDIUM,
        category="controllers",
    ),

    # ── Manifest ──────────────────────────────────────────────────
    MigrationRule(
        id="mfst-001",
        pattern=r"['\"]version['\"]\s*:\s*['\"](\d+)\.0\.",
        replacement=r"'version': '\g<1>.0.", # Note: actual target replacement is done dynamically in engine if we want it perfect, but here we just leave the regex. In engine we could do dynamic replacement. For now we use the rule.
        description="Update module version prefix in __manifest__.py.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18],
        severity=Severity.HIGH,
        category="manifest",
    ),

    # ── Deprecated methods ────────────────────────────────────────
    MigrationRule(
        id="meth-001",
        pattern=r"\.sudo\(\s*\w+\s*\)",
        replacement=".sudo()",
        description="sudo() no longer accepts a user argument — use with_user() instead.",
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
        description="Verify web.assets_backend bundle — v17+ uses new asset format.",
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
    # tree → list: only when target is v18 or newer
    MigrationRule(
        id="xml-002",
        pattern=r"<tree\b",
        replacement="<list",
        description="Replace <tree> with <list> — view renamed in Odoo v18.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17],
        severity=Severity.CRITICAL,
        category="xml",
        min_target_version=OdooVersion.V18,
    ),
    MigrationRule(
        id="xml-003",
        pattern=r"</tree>",
        replacement="</list>",
        description="Replace </tree> with </list> — view renamed in Odoo v18.",
        source_versions=[OdooVersion.V15, OdooVersion.V16, OdooVersion.V17],
        severity=Severity.CRITICAL,
        category="xml",
        min_target_version=OdooVersion.V18,
    ),
]


def get_rules(
    source_version: OdooVersion,
    target_version: OdooVersion | None = None,
) -> list[MigrationRule]:
    """Get all migration rules applicable to a given source→target version pair.

    Args:
        source_version: The Odoo version being migrated FROM.
        target_version: The Odoo version being migrated TO (optional).
                        Rules with min_target_version are only applied when
                        the target is new enough to require them.

    Returns:
        List of applicable MigrationRule objects.
    """
    result = []
    for rule in _RULES:
        if source_version not in rule.source_versions:
            continue
        min_tgt = rule.min_target_version
        if min_tgt is not None and target_version is not None:
            if _VERSION_ORDER.index(target_version) < _VERSION_ORDER.index(min_tgt):
                continue  # Target is too old for this rule
        result.append(rule)
    return result


def get_all_rules() -> list[MigrationRule]:
    """Return every registered migration rule."""
    return list(_RULES)
