"""
OMA Agent — Explainer (Module 09)
LLM-powered explanations of migration changes.
"""

from __future__ import annotations

import logging

from backend.openrouter_client import llm
from backend.prompt_builder import build_explanation_prompt
from backend.schemas import MigrationIssue

logger = logging.getLogger(__name__)


async def explain_migration(
    original_code: str,
    migrated_code: str,
    issues: list[MigrationIssue] | None = None,
) -> str:
    """Generate a human-readable explanation of migration changes.

    Calls the LLM with the original code, new code, and detected issues
    to produce a structured summary.
    """
    logger.info("Generating explanation for migrated code")

    issues_dicts = [i.model_dump() for i in issues] if issues else None

    messages = build_explanation_prompt(
        original=original_code,
        migrated=migrated_code,
        issues=issues_dicts,
    )

    try:
        explanation = await llm.chat_completion(messages, temperature=0.3, max_tokens=1000)
        return explanation
    except Exception as e:
        logger.error("Failed to generate explanation: %s", e)
        return "Explanation could not be generated due to an error."
