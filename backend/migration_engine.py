"""
OMA Agent — Migration Engine
Migrates Odoo source code using the LLM with real GitHub diffs as context.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any

from backend.odoo_brain import fetch_brain_context, format_brain_context
from backend.openrouter_client import llm
from backend.prompt_builder import build_migration_prompt
from backend.schemas import MigrationRequest, MigrationResponse

logger = logging.getLogger(__name__)


async def migrate_code(
    request: MigrationRequest,
    context: dict[str, Any] | None = None,
) -> MigrationResponse:
    """
    Migrate Odoo source code from source_version to target_version.

    Steps:
      1. Fetch real Odoo GitHub diffs (brain) for ground-truth context.
      2. Build LLM prompt with brain diff context injected.
      3. Call LLM and get migrated code.
      4. Generate a unified diff between original and migrated code.
    """
    src = request.source_version.value
    tgt = request.target_version.value
    logger.info("Migrating %s from %s to %s", request.filename, src, tgt)

    # 1. Fetch real Odoo GitHub diffs (brain context)
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
                "Brain loaded %d file diffs for %s (%s → %s)",
                len(brain.file_diffs),
                request.filename,
                src,
                tgt,
            )
    except Exception as e:
        logger.warning("Brain fetch failed, continuing without context: %s", e)

    # 2. Build LLM prompt
    messages = build_migration_prompt(
        source_version=src,
        target_version=tgt,
        filename=request.filename,
        code=request.file_content,
        brain_context=brain_context_str,
    )

    # 3. Call LLM
    try:
        final_code = await llm.chat_completion(messages, temperature=0.1)
    except Exception as e:
        logger.error("LLM migration failed: %s", e)
        # Fall back to original code if LLM fails entirely
        final_code = request.file_content

    # Strip markdown fences if the LLM ignored instructions
    # Handles both leading preamble (e.g., "Here is the migrated code:\n```python")
    # and trailing fences
    # Strip markdown fences — handles preamble, clean fence, or no fence
    fence_match = re.search(r"```[\w-]*\n?(.*?)```", final_code, re.DOTALL)
    if fence_match:
        final_code = fence_match.group(1)
    final_code = final_code.strip()
    if final_code and not final_code.endswith("\n"):
        final_code += "\n"

    # 4. Generate diff
    diff = _generate_diff(request.file_content, final_code, request.filename, src, tgt)

    return MigrationResponse(
        module_name=request.module_name,
        source_version=src,
        target_version=tgt,
        original_code=request.file_content,
        migrated_code=final_code,
        diff=diff,
        issues=[],          # issue_detector removed (rule-based)
        explanation="",     # generated separately by the explainer
    )


def _generate_diff(
    original: str,
    new: str,
    filename: str,
    src: str,
    tgt: str,
) -> str:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{filename} (v{src})",
        tofile=f"b/{filename} (v{tgt})",
        n=3,
    )
    return "".join(diff)
