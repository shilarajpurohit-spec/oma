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
from backend.openrouter_client import llm
from backend.prompt_builder import build_migration_prompt
from backend.schemas import MigrationIssue, MigrationRequest, MigrationResponse

logger = logging.getLogger(__name__)


async def migrate_code(request: MigrationRequest, context: dict[str, Any] | None = None) -> MigrationResponse:
    """Migrate Odoo source code to v19.

    Process:
      1. Apply regex-based static migration rules.
      2. Detect issues on the original code for reporting.
      3. Call the LLM to perform complex/structural migrations.
      4. Generate a unified diff.
    """
    logger.info("Migrating %s from %s to 19.0", request.filename, request.source_version)

    # 1. Apply static rules
    rules = get_rules(request.source_version)
    modified_code = request.file_content

    for rule in rules:
        try:
            modified_code = re.sub(rule.pattern, rule.replacement, modified_code)
        except re.error as e:
            logger.warning("Regex error applying rule %s: %s", rule.id, e)

    # 2. Detect issues on the original code
    issues: list[MigrationIssue] = detect_issues(request.file_content, request.source_version)

    # 3. Call LLM for complex migration
    messages = build_migration_prompt(
        source_version=request.source_version.value,
        filename=request.filename,
        code=modified_code,
    )

    try:
        final_code = await llm.chat_completion(messages, temperature=0.1)
    except Exception as e:
        logger.error("LLM migration failed: %s", e)
        # Fall back to statically modified code if LLM fails
        final_code = modified_code

    # Strip markdown fences if the LLM ignored instructions
    if final_code.startswith("```"):
        final_code = re.sub(r"^```python\s*", "", final_code)
        final_code = re.sub(r"^```\s*", "", final_code)
        final_code = re.sub(r"\s*```\s*$", "", final_code)
        if not final_code.endswith("\n"):
            final_code += "\n"

    # 4. Generate diff
    diff = _generate_diff(request.file_content, final_code, request.filename)

    return MigrationResponse(
        module_name=request.module_name,
        source_version=request.source_version.value,
        target_version="19.0",
        original_code=request.file_content,
        migrated_code=final_code,
        diff=diff,
        issues=issues,
        explanation="",  # Generated separately by the explainer
    )


def _generate_diff(original: str, new: str, filename: str) -> str:
    original_lines = original.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{filename} (v15-18)",
        tofile=f"b/{filename} (v19)",
        n=3,
    )
    return "".join(diff)
