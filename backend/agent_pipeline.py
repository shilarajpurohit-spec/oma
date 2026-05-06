"""
OMA Agent — Agent Pipeline (Module 10)
Orchestrates the full migration flow, multi-file migration, chat, and fix application.
"""

from __future__ import annotations

import asyncio
import logging

from backend.explainer import explain_migration
from backend.migration_engine import migrate_code
from backend.migration_chainer import run_incremental_migration
from backend.openrouter_client import llm
from backend.prompt_builder import build_chat_prompt, build_apply_fix_prompt
from backend.schemas import (
    ApplyFixRequest,
    ApplyFixResponse,
    ChatRequest,
    ChatResponse,
    MigrationRequest,
    MigrationResponse,
    MultiFileMigrationRequest,
    MultiFileMigrationResponse,
    MultiFileMigrationResult,
)
from backend.version_detector import VersionDetectionError, detect_version

logger = logging.getLogger(__name__)

# File extensions we support migrating
_MIGRATABLE_EXTENSIONS = {".py", ".xml", ".js", ".ts", ".csv", ".json"}


async def run_migration(request: MigrationRequest) -> MigrationResponse:
    """Run the full migration pipeline on a single file."""
    # 1. Version Detection (optional cross-check)
    try:
        detected = detect_version(request.file_content, request.filename)
        if detected != request.source_version:
            logger.info(
                "User selected %s but detected %s. Using selected.",
                request.source_version, detected
            )
    except VersionDetectionError:
        pass  # Rely on user's selected version

    # 2. Migration (Rules + LLM + Diff)
    if request.incremental:
        response = await run_incremental_migration(request)
    else:
        response = await migrate_code(request)
    response.filename = request.filename

    # 3. Explanation
    explanation = await explain_migration(
        original_code=response.original_code,
        migrated_code=response.migrated_code,
        issues=response.issues,
    )
    response.explanation = explanation

    return response


async def run_multi_migration(request: MultiFileMigrationRequest) -> MultiFileMigrationResponse:
    """Run the migration pipeline on every file in a module concurrently.

    Files with unsupported extensions are skipped and listed in skipped_files.
    All supported files are migrated concurrently for speed.
    """
    import os

    results: list[MultiFileMigrationResult] = []
    skipped: list[str] = []

    async def _migrate_one(file_item) -> MultiFileMigrationResult | None:
        ext = os.path.splitext(file_item.filename)[1].lower()
        if ext not in _MIGRATABLE_EXTENSIONS:
            skipped.append(file_item.filename)
            return None

        single_req = MigrationRequest(
            module_name=request.module_name,
            source_version=request.source_version,
            target_version=request.target_version,
            filename=file_item.filename,
            file_content=file_item.content,
            incremental=request.incremental,
        )
        try:
            response = await run_migration(single_req)
            return MultiFileMigrationResult(filename=file_item.filename, response=response)
        except Exception as exc:
            logger.error("Failed to migrate %s: %s", file_item.filename, exc)
            skipped.append(file_item.filename)
            return None

    # Concurrently migrate all files
    tasks = [_migrate_one(f) for f in request.files]
    raw_results = await asyncio.gather(*tasks)

    for r in raw_results:
        if r is not None:
            results.append(r)

    total_issues = sum(len(r.response.issues) for r in results)

    return MultiFileMigrationResponse(
        module_name=request.module_name,
        source_version=str(request.source_version.value),
        target_version=str(request.target_version.value),
        results=results,
        total_issues=total_issues,
        skipped_files=skipped,
    )


async def run_apply_fix(request: ApplyFixRequest) -> ApplyFixResponse:
    """Apply a targeted fix to source code using the LLM."""
    messages = build_apply_fix_prompt(
        code=request.code,
        issue_message=request.issue_message,
        suggestion=request.suggestion,
        line=request.line,
    )
    try:
        patched = await llm.chat_completion(messages, temperature=0.1)
        # Sanity check: if LLM returned empty or just whitespace, keep original
        if not patched or not patched.strip():
            return ApplyFixResponse(
                patched_code=request.code,
                applied=False,
                message="LLM returned empty response — original code preserved.",
            )
        return ApplyFixResponse(patched_code=patched.strip(), applied=True)
    except Exception as e:
        logger.error("Apply fix LLM failed: %s", e)
        return ApplyFixResponse(
            patched_code=request.code,
            applied=False,
            message=f"Error applying fix: {e}",
        )


async def run_chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message through the LLM."""
    messages = build_chat_prompt(user_message=request.message, context=request.context)

    try:
        reply = await llm.chat_completion(messages, temperature=0.7)
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error("Chat LLM failed: %s", e)
        return ChatResponse(reply=f"Error communicating with AI assistant: {e}")
