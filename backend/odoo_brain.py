"""
OMA Agent — Odoo Brain

Fetches REAL Odoo source code from GitHub for BOTH the source and target
version branches, computes a unified diff between them for each reference
file, and formats that diff as ground-truth context for the LLM.

Strategy
--------
For a given (source_version, target_version, filename) triple:
  1. Detect file type (xml / python / manifest / js / csv)
  2. Fetch the same reference files from the source AND target branches
  3. Compute a unified diff between source-branch and target-branch versions
  4. Return a formatted BrainContext ready for prompt injection

Cache strategy
--------------
Raw file content is cached on disk under .odoo_brain_cache/ for 24 h.
If GitHub is unreachable the engine continues without brain context.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import NamedTuple

import httpx

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────

ODOO_RAW = "https://raw.githubusercontent.com/odoo/odoo"

CACHE_DIR = Path(__file__).parent.parent / ".odoo_brain_cache"
CACHE_TTL = 60 * 60 * 24  # 24 hours

# Odoo GitHub branch per version
# v19 is not yet on a named branch — fall back to "main"
VERSION_BRANCH: dict[str, str] = {
    "15.0": "15.0",
    "16.0": "16.0",
    "17.0": "17.0",
    "18.0": "18.0",
    "19.0": "main",
}

# Reference files chosen to be small, stable, and representative of
# real migration patterns. Organised by file type.
_REF_FILES: dict[str, list[str]] = {
    "xml": [
        "addons/mail/views/mail_activity_views.xml",
        "addons/web/views/webclient_templates.xml",
    ],
    "python": [
        "addons/mail/models/mail_activity.py",
        "addons/base/models/ir_model.py",
    ],
    "js": [
        "addons/web/static/src/core/utils/arrays.js",
        "addons/web/static/src/core/utils/strings.js",
    ],
    "manifest": [
        "addons/mail/__manifest__.py",
    ],
    "csv": [
        "addons/base/security/ir.model.access.csv",
    ],
}


# ── Cache helpers ──────────────────────────────────────────────────

def _cache_key(branch: str, file_path: str) -> str:
    raw = f"{branch}:{file_path}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def _load_cache(key: str) -> str | None:
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        if time.time() - data["ts"] < CACHE_TTL:
            return data["content"]
    except Exception:
        pass
    return None


def _save_cache(key: str, content: str) -> None:
    try:
        _cache_path(key).write_text(
            json.dumps({"ts": time.time(), "content": content})
        )
    except Exception as e:
        logger.debug("Brain cache write failed: %s", e)


# ── GitHub file fetcher ────────────────────────────────────────────

async def _fetch_raw(branch: str, file_path: str) -> str | None:
    """Fetch a raw file from the Odoo GitHub repo. Uses disk cache."""
    key = _cache_key(branch, file_path)
    cached = _load_cache(key)
    if cached is not None:
        logger.debug("Brain cache hit: %s@%s", file_path, branch)
        return cached

    url = f"{ODOO_RAW}/{branch}/{file_path}"
    logger.info("Brain fetching: %s", url)
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                _save_cache(key, resp.text)
                return resp.text
            logger.warning("Brain fetch %s returned HTTP %s", url, resp.status_code)
    except Exception as e:
        logger.warning("Brain fetch failed for %s: %s", url, e)
    return None


# ── File type detector ─────────────────────────────────────────────

def detect_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".xml":
        return "xml"
    if ext == ".py":
        return "manifest" if "__manifest__" in filename else "python"
    if ext in (".js", ".ts"):
        return "js"
    if ext == ".csv":
        return "csv"
    return "python"


# ── Diff computation ───────────────────────────────────────────────

def _compute_file_diff(
    src_content: str,
    tgt_content: str,
    file_path: str,
    source_branch: str,
    target_branch: str,
) -> str:
    """
    Compute a unified diff between the source-branch and target-branch
    versions of the same reference file.

    This gives the LLM a ground-truth signal: exactly what Odoo itself
    changed in that file between the two versions.
    """
    diff_lines = list(difflib.unified_diff(
        src_content.splitlines(keepends=True),
        tgt_content.splitlines(keepends=True),
        fromfile=f"odoo/{source_branch}/{file_path}",
        tofile=f"odoo/{target_branch}/{file_path}",
        n=5,  # keep 5 lines of context for readability
    ))

    if not diff_lines:
        return ""  # file is identical across branches — no diff to show

    # Cap at 200 diff lines to avoid huge prompts for very large reference files
    MAX_DIFF_LINES = 200
    if len(diff_lines) > MAX_DIFF_LINES:
        diff_lines = diff_lines[:MAX_DIFF_LINES]
        diff_lines.append(
            f"\n... (diff truncated at {MAX_DIFF_LINES} lines for brevity) ...\n"
        )

    return "".join(diff_lines)


# ── Public API ─────────────────────────────────────────────────────

class BrainContext(NamedTuple):
    """Holds real Odoo file diffs and source/target reference code."""
    file_type: str
    source_version: str
    target_version: str
    # List of (file_path, diff_text) for files that changed between branches
    file_diffs: list[tuple[str, str]]


async def fetch_brain_context(
    source_version: str,
    target_version: str,
    filename: str,
) -> BrainContext | None:
    """
    Fetch real Odoo reference files from GitHub for both branches,
    compute a unified diff between them, and return a BrainContext.

    The diffs show the LLM exactly what Odoo changed in its own codebase
    between the two versions — far more informative than raw snippets.

    Args:
        source_version: e.g. "15.0"
        target_version: e.g. "18.0" or "19.0"
        filename: e.g. "views.xml" — used to detect file type

    Returns:
        BrainContext with file diffs, or None if GitHub is unreachable.
    """
    file_type = detect_file_type(filename)
    ref_files = _REF_FILES.get(file_type, _REF_FILES["python"])

    source_branch = VERSION_BRANCH.get(source_version)
    target_branch = VERSION_BRANCH.get(target_version)

    if not source_branch or not target_branch:
        logger.warning(
            "Brain: no branch mapping for versions %s / %s",
            source_version, target_version,
        )
        return None

    file_diffs: list[tuple[str, str]] = []

    for ref_file in ref_files:
        src_content = await _fetch_raw(source_branch, ref_file)
        tgt_content = await _fetch_raw(target_branch, ref_file)

        if not src_content or not tgt_content:
            logger.debug("Brain: skipping %s (fetch failed for one branch)", ref_file)
            continue

        diff_text = _compute_file_diff(
            src_content,
            tgt_content,
            ref_file,
            source_branch,
            target_branch,
        )

        if diff_text:
            file_diffs.append((ref_file, diff_text))
            logger.info("Brain diff: %s (%d diff lines)", ref_file, diff_text.count("\n"))
        else:
            logger.debug("Brain: %s is identical across branches — skipped", ref_file)

    if not file_diffs:
        logger.warning("Brain: no diffs found — continuing without context")
        return None

    return BrainContext(
        file_type=file_type,
        source_version=source_version,
        target_version=target_version,
        file_diffs=file_diffs,
    )


def format_brain_context(ctx: BrainContext) -> str:
    """
    Format a BrainContext into a block suitable for injection into the
    LLM system prompt.

    The formatted block shows the LLM exactly what Odoo itself changed in
    real reference files between the two branches — ground-truth context.
    """
    src_branch = VERSION_BRANCH.get(ctx.source_version, ctx.source_version)
    tgt_branch = VERSION_BRANCH.get(ctx.target_version, ctx.target_version)

    parts: list[str] = [
        "=== REAL ODOO CODE CHANGES (GitHub ground truth) ===",
        f"File type  : {ctx.file_type}",
        f"Migrating  : Odoo {ctx.source_version} → {ctx.target_version}",
        f"Source ref : github.com/odoo/odoo  branch: {src_branch}",
        f"Target ref : github.com/odoo/odoo  branch: {tgt_branch}",
        "",
        "The diffs below are taken DIRECTLY from the official Odoo repository.",
        "Each diff shows what Odoo itself changed in a real file between these two versions.",
        "Use these as ground truth to understand what patterns need to change.",
        "",
    ]

    for file_path, diff_text in ctx.file_diffs:
        parts.append(f"--- diff: {file_path} ---")
        parts.append(diff_text)
        parts.append("")

    parts.append("=== END OF REAL ODOO CODE CHANGES ===")
    return "\n".join(parts)
