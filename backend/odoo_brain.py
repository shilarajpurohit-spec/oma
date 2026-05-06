"""
OMA Agent — Odoo Brain (Module 25)

Fetches real Odoo source code from GitHub as reference context for the LLM.
Instead of static rule strings, the brain provides ACTUAL before/after code
examples from the official Odoo repository, making the LLM migration far
more accurate and grounded.

Brain strategy
--------------
For a given (source_version, target_version, filename) triple:
  1. Detect file type (xml / python / manifest / js / csv)
  2. Fetch relevant reference files from the source branch
  3. Fetch the same files from the target branch
  4. Also attempt to fetch the git diff between branches for dense signal
  5. Extract the most migration-relevant snippets from each file
  6. Return a formatted BrainContext ready for prompt injection

Cache strategy
--------------
Snippets are cached on disk under .odoo_brain_cache/ for 24 h.
If GitHub is unreachable the engine continues without brain context.
"""

from __future__ import annotations

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
ODOO_COMPARE = "https://github.com/odoo/odoo/compare"

CACHE_DIR = Path(__file__).parent.parent / ".odoo_brain_cache"
CACHE_TTL = 60 * 60 * 24  # 24 hours in seconds

# Odoo GitHub branch per version
# v19 is not yet public — fallback to "main" (closest to v19)
VERSION_BRANCH: dict[str, str] = {
    "15.0": "15.0",
    "16.0": "16.0",
    "17.0": "17.0",
    "18.0": "18.0",
    "19.0": "main",   # v19 not yet on a named branch — use main
}

# ── Reference file map ────────────────────────────────────────────
# Organised by file type so the brain fetches the most relevant examples.
# Files chosen for being small, stable, and demonstrating key patterns.

_REF_FILES: dict[str, list[str]] = {
    "xml": [
        "addons/note/views/note_views.xml",          # small, has tree/list
        "addons/base/views/res_lang_views.xml",       # base tree view
    ],
    "python": [
        "addons/note/models/note.py",                # simple model, api decorators
        "addons/base/models/res_lang.py",            # fields, compute
    ],
    "js": [
        "addons/web/static/src/core/utils/arrays.js",
        "addons/web/static/src/views/list/list_renderer.js",
    ],
    "manifest": [
        "addons/note/__manifest__.py",
        "addons/base/__manifest__.py",
    ],
    "csv": [
        "addons/base/security/ir.model.access.csv",
    ],
}

# How many lines to keep per snippet (keeps prompt token count sane)
_MAX_LINES = 60


# ── Cache helpers ──────────────────────────────────────────────────

def _cache_key(source_version: str, target_version: str, path: str) -> str:
    raw = f"{source_version}:{target_version}:{path}"
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


# ── GitHub fetcher ─────────────────────────────────────────────────

async def _fetch_raw(
    source_version: str,
    target_version: str,
    branch: str,
    file_path: str,
) -> str | None:
    """Fetch a raw file from the Odoo GitHub repo, with version-pair cache."""
    key = _cache_key(source_version, target_version, f"{branch}:{file_path}")
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
                content = resp.text
                _save_cache(key, content)
                return content
            logger.warning("Brain fetch %s returned HTTP %s", url, resp.status_code)
    except Exception as e:
        logger.warning("Brain fetch failed for %s: %s", url, e)
    return None


# ── Snippet extractor ──────────────────────────────────────────────

def _extract_snippet(content: str, file_type: str, max_lines: int = _MAX_LINES) -> str:
    """Extract the most migration-relevant portion of a file."""
    lines = content.splitlines()

    if file_type == "xml":
        # Find first <tree> or <list> block and grab context around it
        for i, line in enumerate(lines):
            if re.search(r"<(tree|list)\b", line):
                start = max(0, i - 3)
                end = min(len(lines), i + max_lines)
                return "\n".join(lines[start:end])
        return "\n".join(lines[:max_lines])

    if file_type == "python":
        # Find first class definition and grab from there
        for i, line in enumerate(lines):
            if re.match(r"^class\s+\w+\(", line):
                start = max(0, i - 2)
                end = min(len(lines), i + max_lines)
                return "\n".join(lines[start:end])
        return "\n".join(lines[:max_lines])

    if file_type in ("manifest", "csv"):
        return "\n".join(lines[:max_lines])

    if file_type == "js":
        # Find first export or class keyword
        for i, line in enumerate(lines):
            if re.match(r"^(export|class)\s", line):
                start = max(0, i - 2)
                end = min(len(lines), i + max_lines)
                return "\n".join(lines[start:end])
        return "\n".join(lines[:max_lines])

    return "\n".join(lines[:max_lines])


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


# ── Public API ─────────────────────────────────────────────────────

class BrainContext(NamedTuple):
    """Holds before/after reference snippets from real Odoo source."""
    file_type: str
    source_version: str
    target_version: str
    source_snippets: list[tuple[str, str]]   # (file_path, snippet)
    target_snippets: list[tuple[str, str]]   # (file_path, snippet)


async def fetch_brain_context(
    source_version: str,
    target_version: str,
    filename: str,
) -> BrainContext | None:
    """
    Fetch real Odoo reference code from GitHub for BOTH the source version
    and the target version.

    Args:
        source_version: e.g. "15.0"
        target_version: e.g. "18.0" or "19.0"
        filename: e.g. "views.xml" — used to detect file type

    Returns:
        BrainContext with before/after snippets, or None if GitHub unreachable.
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

    source_snippets: list[tuple[str, str]] = []
    target_snippets: list[tuple[str, str]] = []

    for ref_file in ref_files:
        # Fetch from source version branch
        src_content = await _fetch_raw(source_version, target_version, source_branch, ref_file)
        if src_content:
            snippet = _extract_snippet(src_content, file_type)
            source_snippets.append((ref_file, snippet))

        # Fetch from target version branch
        tgt_content = await _fetch_raw(source_version, target_version, target_branch, ref_file)
        if tgt_content:
            snippet = _extract_snippet(tgt_content, file_type)
            target_snippets.append((ref_file, snippet))

    if not source_snippets and not target_snippets:
        logger.warning("Brain: no snippets fetched — continuing without context")
        return None

    return BrainContext(
        file_type=file_type,
        source_version=source_version,
        target_version=target_version,
        source_snippets=source_snippets,
        target_snippets=target_snippets,
    )


def format_brain_context(ctx: BrainContext) -> str:
    """
    Format a BrainContext into a human-readable block suitable for
    injection into the LLM system prompt.
    """
    src_branch = VERSION_BRANCH.get(ctx.source_version, ctx.source_version)
    tgt_branch = VERSION_BRANCH.get(ctx.target_version, ctx.target_version)

    parts: list[str] = [
        "=== REAL ODOO SOURCE CODE REFERENCE ===",
        f"File type  : {ctx.file_type}",
        f"Migrating  : Odoo {ctx.source_version} → {ctx.target_version}",
        f"Source ref : github.com/odoo/odoo (branch: {src_branch})",
        f"Target ref : github.com/odoo/odoo (branch: {tgt_branch})",
        "",
        "The following snippets are taken DIRECTLY from the official Odoo repository.",
        "Use them as ground truth for what the migrated code must look like.",
        "",
    ]

    if ctx.source_snippets:
        parts.append(f"--- ODOO {ctx.source_version} (BEFORE / OLD STYLE) ---")
        for path, snippet in ctx.source_snippets:
            parts.append(f"# {path}")
            parts.append(snippet)
            parts.append("")

    if ctx.target_snippets:
        parts.append(f"--- ODOO {ctx.target_version} (AFTER / NEW STYLE — TARGET PATTERN) ---")
        for path, snippet in ctx.target_snippets:
            parts.append(f"# {path}")
            parts.append(snippet)
            parts.append("")

    parts.append("=== END OF REFERENCE ===")
    return "\n".join(parts)
