"""
OMA Agent — Prompt Builder (Module 11)
System prompt templates for LLM calls, with version-specific Odoo 19 migration context.
"""

from __future__ import annotations


# ── Odoo 19 migration context by source version ───────────────────

_VERSION_CONTEXT: dict[str, str] = {
    "15.0": """
Key changes from Odoo 15 → 19:
- CRITICAL: Replace 'from openerp' with 'from odoo' everywhere.
- CRITICAL: Replace osv.osv and osv.Model with models.Model.
- CRITICAL: Replace self.pool['model'] registry access with self.env['model'].
- HIGH: .sudo(user) is removed — use .with_user(user).sudo() instead.
- HIGH: OWL1 (owl.Component, owl.tags) must be rewritten for OWL2 (setup(), useState, hooks).
- HIGH: Javascript modules: replace 'odoo.define(...)' with ES module syntax.
- MEDIUM: fields_get / fields_get_keys API has changed.
- MEDIUM: __manifest__ 'qweb' key removed — move templates to 'assets' bundles.
- MEDIUM: web.assets_backend / web.assets_frontend bundle names changed.
- MEDIUM: ir.actions.act_window view_type field removed from XML.
- LOW: Module version in manifest must be updated to 19.0.x.x.x.
- LOW: Test classes should extend common.TransactionCase or common.SavepointCase.
""",
    "16.0": """
Key changes from Odoo 16 → 19:
- HIGH: .sudo(user) is removed — use .with_user(user).sudo() instead.
- HIGH: OWL1 patterns (if still present) must be updated to OWL2.
- HIGH: Javascript legacy 'odoo.define(...)' modules → ES modules.
- MEDIUM: __manifest__ 'qweb' key fully removed in v17 — use 'assets' bundles.
- MEDIUM: Some deprecated _compute_ method signatures changed (multi=True removed).
- MEDIUM: Spreadsheet/Report QWeb template namespaces updated.
- LOW: Module version in manifest must be updated to 19.0.x.x.x.
- LOW: Python 3.12 compatibility required (match-case, walrus operator patterns OK).
""",
    "17.0": """
Key changes from Odoo 17 → 19:
- HIGH: OWL2 was adopted in v17 but APIs evolved — verify owl.reactive, useState imports.
- HIGH: 'website' and 'portal' view keys in manifest changed structure.
- MEDIUM: ir.model.access CSV format changed (no 'id' column required now).
- MEDIUM: account.move no longer has type field — check journal/move_type instead.
- MEDIUM: Company-dependent field setup may require updated company_dependent=True param.
- LOW: Module version in manifest must be updated to 19.0.x.x.x.
- LOW: Python type hints should use built-in generics (list, dict) not typing.List/Dict.
""",
    "18.0": """
Key changes from Odoo 18 → 19:
- MEDIUM: Some internal OWL component prop types changed — verify @Component decorators.
- MEDIUM: ir.attachment 'datas_fname' field removed — use 'name' only.
- MEDIUM: Spreadsheet bundle and spreadsheet component imports may have moved.
- MEDIUM: stock.move and stock.quant have new state transitions in v19.
- LOW: Module version in manifest must be updated to 19.0.x.x.x.
- LOW: Verify any hard-coded Odoo version strings are updated across the module.
""",
}

_ODOO19_GENERAL_RULES = """
General Odoo 19 migration rules (apply to ALL versions):
- Always update _description = "..." if missing (required in v19, generates warning otherwise).
- Use `fields.Json` instead of `fields.Serialized` for JSON storage fields.
- For compute fields: use 'compute_sudo=True' explicitly if the computation needs elevated rights.
- Replace any 'api.multi' decorator (fully gone since v14) with nothing — remove the decorator.
- Replace 'api.one' decorator with 'api.multi'-style loops or set-based operations.
- For XML: replace deprecated 'string' attribute on <field> tags with 'label'.
- Always add missing 'groups' attribute or explicit access rules for new models.
- Verify __manifest__.py 'depends' list includes all transitively required modules.
"""


# ── Migration prompt ──────────────────────────────────────────────

def build_migration_prompt(
    source_version: str,
    filename: str,
    code: str,
) -> list[dict[str, str]]:
    """Build messages for migrating Odoo code to v19.

    Includes version-specific migration context so the LLM can make
    targeted, accurate changes beyond generic patterns.

    Returns:
        A list of {"role": ..., "content": ...} dicts ready for the LLM.
    """
    version_ctx = _VERSION_CONTEXT.get(source_version, "")

    system = (
        "You are an expert Odoo developer specialising in module migration. "
        "Your task is to migrate the given Odoo module code to Odoo 19.\n\n"
        "Rules:\n"
        "1. Return ONLY the migrated Python/XML/JS code — no explanations, no markdown fences.\n"
        "2. Preserve the original code structure, comments, and formatting as much as possible.\n"
        "3. Apply ALL necessary API changes between the source version and Odoo 19.\n"
        "4. Update deprecated imports, method signatures, field definitions, and decorators.\n"
        "5. Ensure the migrated code is syntactically valid Python (or valid XML/JS if applicable).\n"
        "6. If the code uses OWL components (JS/XML), migrate from OWL1 to OWL2 patterns.\n"
        "7. Update manifest version and dependency declarations if present.\n"
        "8. Do NOT invent new functionality — only migrate existing code.\n"
        f"\n{_ODOO19_GENERAL_RULES}"
        f"\n{version_ctx}"
    )

    user = (
        f"Migrate the following Odoo {source_version} code to Odoo 19.\n"
        f"File: {filename}\n\n"
        f"```\n{code}\n```"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── Explanation prompt ────────────────────────────────────────────

def build_explanation_prompt(
    original: str,
    migrated: str,
    issues: list[dict] | None = None,
) -> list[dict[str, str]]:
    """Build messages for explaining migration changes.

    Args:
        original: The original source code.
        migrated: The migrated code.
        issues: Optional list of issue dicts (serialised MigrationIssue).

    Returns:
        Message list for the LLM.
    """
    system = (
        "You are an expert Odoo developer. Explain the migration changes "
        "in clear, concise language that a mid-level developer can understand.\n\n"
        "Structure your explanation as:\n"
        "1. **Summary** — one-paragraph overview of what changed.\n"
        "2. **Key Changes** — bullet list of each significant change and why it was needed.\n"
        "3. **Breaking Changes** — anything that may require manual review.\n"
        "4. **Recommendations** — optional tips for the developer."
    )

    issues_text = ""
    if issues:
        issues_text = "\n\nDetected issues:\n"
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "medium")
            msg = issue.get("message", "")
            issues_text += f"  {i}. [{sev.upper()}] {msg}\n"

    user = (
        "Here is the original code:\n"
        f"```\n{original}\n```\n\n"
        "Here is the migrated code:\n"
        f"```\n{migrated}\n```"
        f"{issues_text}"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── Apply Fix prompt ──────────────────────────────────────────────

def build_apply_fix_prompt(
    code: str,
    issue_message: str,
    suggestion: str,
    line: int | None = None,
) -> list[dict[str, str]]:
    """Build messages for applying a specific fix to code.

    Args:
        code: The full current source code.
        issue_message: The issue description.
        suggestion: The fix suggestion/hint.
        line: Optional line number where the issue was detected.

    Returns:
        Message list for the LLM.
    """
    system = (
        "You are an expert Odoo developer. The user has a specific issue in their code "
        "and wants you to apply a targeted fix.\n\n"
        "Rules:\n"
        "1. Return ONLY the complete, corrected source code — no explanations, no markdown fences.\n"
        "2. Apply ONLY the fix described in the suggestion. Do not change anything else.\n"
        "3. Preserve all comments, formatting, and unrelated code exactly.\n"
        "4. Ensure the result is syntactically valid.\n"
        "5. If the fix cannot be applied safely, return the original code unchanged."
    )

    line_hint = f" (detected at line {line})" if line else ""
    user = (
        f"Issue{line_hint}: {issue_message}\n"
        f"Fix to apply: {suggestion}\n\n"
        f"Current code:\n```\n{code}\n```"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── Chat prompt ───────────────────────────────────────────────────

def build_chat_prompt(
    user_message: str,
    context: str | None = None,
) -> list[dict[str, str]]:
    """Build messages for the agent chat interface.

    Args:
        user_message: The user's question / message.
        context: Optional code context the user has provided.

    Returns:
        Message list for the LLM.
    """
    system = (
        "You are OMA Agent, an AI assistant specialising in Odoo module migration "
        "from versions 15–18 to Odoo 19. You help developers understand migration "
        "changes, debug issues, and write compatible code.\n\n"
        "Be concise, accurate, and provide code examples when helpful. "
        "If you are unsure about something, say so rather than guessing.\n\n"
        f"{_ODOO19_GENERAL_RULES}"
    )

    user_parts = [user_message]
    if context:
        user_parts.append(f"\n\nCode context:\n```\n{context}\n```")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "".join(user_parts)},
    ]
