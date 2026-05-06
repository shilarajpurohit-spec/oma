"""
OMA Agent — Prompt Builder (Module 11)
System prompt templates for LLM calls, with dynamic version-pair migration context.

The _VERSION_PAIR_CONTEXT matrix holds per-(source,target) migration notes.
For any pair not explicitly listed, _build_version_context() accumulates all
intermediate step rules automatically (e.g. 15→18 = 15→16 + 16→17 + 17→18).
"""

from __future__ import annotations


# ── Step-by-step migration rules ─────────────────────────────────
# Keyed as (source, target) for ADJACENT version steps only.
# Larger jumps are assembled automatically by _build_version_context().

_STEP_CONTEXT: dict[tuple[str, str], str] = {

    # ── v15 → v16 ────────────────────────────────────────────────
    ("15.0", "16.0"): """
Changes from Odoo 15 → 16:
- CRITICAL: Replace 'from openerp' with 'from odoo' everywhere.
- CRITICAL: Replace osv.osv and osv.Model with models.Model.
- CRITICAL: Replace self.pool['model'] registry access with self.env['model'].
- HIGH: .sudo(user) is removed — use .with_user(user).sudo() instead.
- HIGH: OWL1 (owl.Component, owl.tags) must be rewritten for OWL2 (setup(), useState, hooks).
- HIGH: Replace 'odoo.define(...)' Javascript modules with ES module syntax.
- MEDIUM: __manifest__ 'qweb' key removed — move templates to 'assets' bundles.
- MEDIUM: web.assets_backend / web.assets_frontend bundle names updated.
- MEDIUM: ir.actions.act_window 'view_type' field removed from XML.
- LOW: Update module version in __manifest__.py to 16.0.x.x.x.
""",

    # ── v16 → v17 ────────────────────────────────────────────────
    ("16.0", "17.0"): """
Changes from Odoo 16 → 17:
- HIGH: OWL2 was fully adopted — verify owl.reactive, useState, onWillStart hooks.
- HIGH: 'website' and 'portal' view keys in manifest changed structure.
- MEDIUM: ir.model.access CSV format changed (no 'id' column required now).
- MEDIUM: account.move no longer has 'type' field — check journal/move_type instead.
- MEDIUM: Some deprecated _compute_ method signatures changed (multi=True removed).
- MEDIUM: Spreadsheet/Report QWeb template namespaces updated.
- LOW: Update module version in __manifest__.py to 17.0.x.x.x.
- LOW: Python type hints should use built-in generics (list, dict) not typing.List/Dict.
""",

    # ── v17 → v18 ────────────────────────────────────────────────
    ("17.0", "18.0"): """
Changes from Odoo 17 → 18:
- CRITICAL: Replace ALL <tree> tags with <list> and </tree> with </list> in XML views.
            Odoo v18 renamed the tree view type to list. Both opening AND closing tags must change.
- MEDIUM: Company-dependent field setup may require updated company_dependent=True param.
- MEDIUM: ir.attachment 'datas_fname' field removed — use 'name' field only.
- MEDIUM: Some internal OWL component prop types changed — verify @Component decorators.
- MEDIUM: Spreadsheet bundle and spreadsheet component imports may have moved.
- LOW: Update module version in __manifest__.py to 18.0.x.x.x.
""",

    # ── v18 → v19 ────────────────────────────────────────────────
    ("18.0", "19.0"): """
Changes from Odoo 18 → 19:
- MEDIUM: stock.move and stock.quant have new state transitions in v19.
- MEDIUM: Some internal OWL component prop types changed — verify @Component decorators.
- MEDIUM: Spreadsheet bundle and component imports may have moved.
- LOW: Update module version in __manifest__.py to 19.0.x.x.x.
- LOW: Verify any hard-coded Odoo version strings are updated across the module.
""",
}

# Ordered version list — used to walk intermediate steps
_VERSION_ORDER = ["15.0", "16.0", "17.0", "18.0", "19.0"]


def _build_version_context(source_version: str, target_version: str) -> str:
    """
    Accumulate migration notes for all intermediate steps between
    source_version and target_version.

    e.g. 15→18 = notes(15→16) + notes(16→17) + notes(17→18)
    """
    try:
        src_idx = _VERSION_ORDER.index(source_version)
        tgt_idx = _VERSION_ORDER.index(target_version)
    except ValueError:
        return ""

    parts: list[str] = [
        f"Migration from Odoo {source_version} → {target_version} "
        f"(accumulated rules for all {tgt_idx - src_idx} intermediate step(s)):"
    ]

    for i in range(src_idx, tgt_idx):
        step_src = _VERSION_ORDER[i]
        step_tgt = _VERSION_ORDER[i + 1]
        notes = _STEP_CONTEXT.get((step_src, step_tgt), "")
        if notes:
            parts.append(notes.strip())

    return "\n\n".join(parts)


# ── General rules (all version pairs) ────────────────────────────
_ODOO_GENERAL_RULES = """
General rules (apply to ALL Odoo migrations):
- Always update _description = "..." if missing (required in v16+, generates warning otherwise).
- Use `fields.Json` instead of `fields.Serialized` for JSON storage fields.
- For compute fields: use 'compute_sudo=True' explicitly if the computation needs elevated rights.
- Remove any 'api.multi' decorator (fully gone since v14).
- Remove any 'api.one' decorator — rewrite as set-based operation.
- For XML: replace deprecated 'string' attribute on <field> tags with 'label'.
- Always add missing 'groups' attribute or explicit access rules for new models.
- Verify __manifest__.py 'depends' list includes all transitively required modules.
"""


# ── Migration prompt ──────────────────────────────────────────────

def build_migration_prompt(
    source_version: str,
    target_version: str,
    filename: str,
    code: str,
    brain_context: str | None = None,
) -> list[dict[str, str]]:
    """Build messages for migrating Odoo code from source_version to target_version.

    Includes:
    - Accumulated version-pair migration rules for all intermediate steps
    - Optional real Odoo source code snippets fetched from GitHub (brain context)
    - General rules that apply to all migrations

    The brain snippets act as ground-truth few-shot examples, making
    the LLM migration far more accurate than static rule strings alone.

    Args:
        source_version: e.g. "15.0", "17.0"
        target_version: e.g. "17.0", "19.0"
        filename: e.g. "models.py", "views.xml"
        code: the code to migrate
        brain_context: optional formatted string from odoo_brain.format_brain_context()

    Returns:
        A list of {"role": ..., "content": ...} dicts ready for the LLM.
    """
    version_ctx = _build_version_context(source_version, target_version)

    brain_section = (
        f"\n\n{brain_context}\n\n"
        "Use the REAL ODOO SOURCE CODE REFERENCE above as your primary guide. "
        "The new-style snippets show exactly what the migrated output must look like."
        if brain_context
        else ""
    )

    system = (
        f"You are an expert Odoo developer specialising in module migration. "
        f"Your task is to migrate the given Odoo {source_version} code to Odoo {target_version}.\n\n"
        "Rules:\n"
        "1. Return ONLY the migrated Python/XML/JS code — no explanations, no markdown fences.\n"
        "2. Preserve the original code structure, comments, and formatting as much as possible.\n"
        f"3. Apply ALL necessary API changes between Odoo {source_version} and {target_version}.\n"
        "4. Update deprecated imports, method signatures, field definitions, and decorators.\n"
        "5. Ensure the migrated code is syntactically valid Python (or valid XML/JS if applicable).\n"
        "6. If the code uses OWL components (JS/XML), apply the appropriate OWL migration.\n"
        "7. Update manifest version and dependency declarations if present.\n"
        "8. Do NOT invent new functionality — only migrate existing code.\n"
        "9. When real Odoo reference code is provided below, treat it as ground truth "
        "and mirror its patterns exactly in your output.\n"
        f"{brain_section}"
        f"\n{_ODOO_GENERAL_RULES}"
        f"\n{version_ctx}"
    )

    user = (
        f"Migrate the following Odoo {source_version} code to Odoo {target_version}.\n"
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
    source_version: str = "source",
    target_version: str = "19.0",
    issues: list[dict] | None = None,
) -> list[dict[str, str]]:
    """Build messages for explaining migration changes."""
    system = (
        "You are an expert Odoo developer. Explain the migration changes "
        "in clear, concise language that a mid-level developer can understand.\n\n"
        "Structure your explanation as:\n"
        f"1. **Summary** — one-paragraph overview of what changed (Odoo {source_version} → {target_version}).\n"
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
    """Build messages for applying a specific fix to code."""
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
    """Build messages for the agent chat interface."""
    system = (
        "You are OMA Agent, an AI assistant specialising in Odoo module migration "
        "across versions 15, 16, 17, 18, and 19. You help developers understand migration "
        "changes, debug issues, and write compatible code.\n\n"
        "Be concise, accurate, and provide code examples when helpful. "
        "If you are unsure about something, say so rather than guessing.\n\n"
        f"{_ODOO_GENERAL_RULES}"
    )

    user_parts = [user_message]
    if context:
        user_parts.append(f"\n\nCode context:\n```\n{context}\n```")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "".join(user_parts)},
    ]
