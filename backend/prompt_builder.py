"""
OMA Agent — Prompt Builder
System prompt templates for LLM calls.
"""

from __future__ import annotations


# ── Migration prompt ──────────────────────────────────────────────

def build_migration_prompt(
    source_version: str,
    target_version: str,
    filename: str,
    code: str,
    brain_context: str | None = None,
) -> list[dict[str, str]]:
    """
    Build the LLM messages for migrating Odoo code.

    When brain_context is provided it contains real unified diffs from the
    official Odoo repository showing exactly what changed between the two
    branches. The LLM should use these as ground truth.

    Args:
        source_version: e.g. "15.0", "17.0"
        target_version: e.g. "17.0", "19.0"
        filename: e.g. "models.py", "views.xml"
        code: the code to migrate
        brain_context: formatted string from odoo_brain.format_brain_context()

    Returns:
        A list of {"role": ..., "content": ...} dicts ready for the LLM.
    """
    actual_type = _detect_content_type(code, filename)
    brain_section = (
        f"\n\n{brain_context}\n\n"
        "IMPORTANT: The diffs above are taken directly from the official Odoo repository. "
        "They show exactly what Odoo itself changed between these two versions. "
        "Study them carefully and apply the same patterns to the user's code."
        if brain_context
        else ""
    )

    system = (
        f"You are an expert Odoo developer specialising in module migration.\n"
        f"Your task is to migrate the given Odoo {source_version} code to Odoo {target_version}.\n\n"
        f"CRITICAL: The input is a {actual_type} file. "
        f"You MUST output migrated {actual_type} code ONLY.\n"
        f"Do NOT convert, rewrite, or change the file type under any circumstances.\n"
        f"If the input is XML, output XML. If Python, output Python. If JS, output JS.\n\n"
        "Rules:\n"
        "1. Return ONLY the migrated code — no explanations, no markdown fences.\n"
        "2. Preserve the original code structure, comments, and formatting.\n"
        f"3. Apply ALL necessary API changes between Odoo {source_version} and {target_version}.\n"
        "4. Do NOT invent new functionality — only migrate existing code.\n"
        "5. Do NOT generate model classes from XML view files.\n"
        "6. Do NOT generate view XML from Python model files.\n"
        f"{brain_section}"
    )

    user = (
        f"Migrate the following Odoo {source_version} {actual_type} code to Odoo {target_version}.\n"
        f"File: {filename}\n"
        f"Content type: {actual_type}\n\n"
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
        "If you are unsure about something, say so rather than guessing."
    )

    user_parts = [user_message]
    if context:
        user_parts.append(f"\n\nCode context:\n```\n{context}\n```")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "".join(user_parts)},
    ]


def _detect_content_type(code: str, filename: str) -> str:
    """Detect actual content type from content first, filename as fallback."""
    stripped = code.strip()

    # Detect from content
    if stripped.startswith("<") and ("<record" in stripped or "<odoo" in stripped
                                      or "<kanban" in stripped or "<form" in stripped
                                      or "<tree" in stripped or "<?xml" in stripped):
        return "XML"
    if stripped.startswith("{") or stripped.startswith("["):
        return "JSON"
    if "def " in stripped or "class " in stripped or "import " in stripped:
        return "Python"
    if "owl" in stripped or "useState" in stripped or "Component" in stripped:
        return "JavaScript"
    # Fallback to filename extension
    import os
    ext = os.path.splitext(filename)[1].lower()
    return {".xml": "XML", ".py": "Python", ".js": "JavaScript",
            ".ts": "TypeScript", ".csv": "CSV", ".json": "JSON"}.get(ext, "Python")