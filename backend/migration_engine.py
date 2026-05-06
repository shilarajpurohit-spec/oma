"""
OMA Agent — Migration Engine (Module 07)
Code transformer that applies rules and LLM calls.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any

from backend.issue_detector import detect_issues
from backend.migration_rules import get_rules
from backend.odoo_brain import fetch_brain_context, format_brain_context
from backend.openrouter_client import llm
from backend.prompt_builder import build_migration_prompt
from backend.schemas import MigrationIssue, MigrationRequest, MigrationResponse

logger = logging.getLogger(__name__)


async def migrate_code(request: MigrationRequest, context: dict[str, Any] | None = None) -> MigrationResponse:
    """Migrate Odoo source code from source_version to target_version.

    Process:
      1. Apply regex-based static migration rules.
      2. Detect issues on the original code for reporting.
      3. Fetch real Odoo GitHub snippets via the agent brain.
      4. Call the LLM with brain context injected into the prompt.
      5. Generate a unified diff.
    """
    src = request.source_version.value
    tgt = request.target_version.value
    logger.info("Migrating %s from %s to %s", request.filename, src, tgt)

    # 1. Apply static rules (only rules applicable to this source→target range)
    rules = get_rules(request.source_version, request.target_version)
    modified_code = request.file_content

    for rule in rules:
        try:
            modified_code = re.sub(rule.pattern, rule.replacement, modified_code)
        except re.error as e:
            logger.warning("Regex error applying rule %s: %s", rule.id, e)

    # 2. Detect issues on the original code
    issues: list[MigrationIssue] = detect_issues(request.file_content, request.source_version)

    # 3. Fetch real Odoo reference code from GitHub (agent brain)
    brain_context_str: str | None = None
    try:
        brain = await fetch_brain_context(
            source_version=src,
            target_version=tgt,
            filename=request.filename,
        )
        if brain:
            brain_context_str = format_brain_context(brain)
            logger.info(
                "Brain loaded %d source + %d target snippets for %s (%s→%s)",
                len(brain.source_snippets),
                len(brain.target_snippets),
                request.filename,
                src,
                tgt,
            )
    except Exception as e:
        logger.warning("Brain fetch failed, continuing without context: %s", e)

    # 4. Call LLM for complex migration (with brain context injected)
    messages = build_migration_prompt(
        source_version=src,
        target_version=tgt,
        filename=request.filename,
        code=modified_code,
        brain_context=brain_context_str,
    )

    try:
        final_code = await llm.chat_completion(messages, temperature=0.1)
    except Exception as e:
        logger.error("LLM migration failed: %s", e)
        # Fall back to statically modified code if LLM fails
        final_code = modified_code

    # Strip markdown fences if the LLM ignored instructions
    if final_code.startswith("```"):
        final_code = re.sub(r"^```\w*\s*", "", final_code)
        final_code = re.sub(r"\s*```\s*$", "", final_code)
        if not final_code.endswith("\n"):
            final_code += "\n"

    # 5. Generate diff
    diff = _generate_diff(request.file_content, final_code, request.filename, src, tgt)

    return MigrationResponse(
        module_name=request.module_name,
        source_version=src,
        target_version=tgt,
        original_code=request.file_content,
        migrated_code=final_code,
        diff=diff,
        issues=issues,
        explanation="",  # Generated separately by the explainer
    )


def _generate_diff(original: str, new: str, filename: str, src: str, tgt: str) -> str:
    original_lines = original.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{filename} (v{src})",
        tofile=f"b/{filename} (v{tgt})",
        n=3,
    )
    return "".join(diff)
