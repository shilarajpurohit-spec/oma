"""
OMA Agent — Version Detector (Module 04)
Auto-detect Odoo source version from code patterns.
"""

from __future__ import annotations

import re

from backend.schemas import OdooVersion


class VersionDetectionError(Exception):
    """Raised when the source Odoo version cannot be determined."""


# ── Version-specific patterns (checked in order, newest first) ────

_VERSION_PATTERNS: list[tuple[OdooVersion, list[re.Pattern]]] = [
    (
        OdooVersion.V18,
        [
            re.compile(r"""['"]version['"]\s*:\s*['"]18\.0"""),
            re.compile(r"from\s+odoo\.tools\.json\b"),
            re.compile(r"odoo\.upgrade"),
        ],
    ),
    (
        OdooVersion.V17,
        [
            re.compile(r"""['"]version['"]\s*:\s*['"]17\.0"""),
            re.compile(r"\bComponent\b.*\bsetup\b"),  # OWL2 pattern
            re.compile(r"from\s+odoo\.addons\.web\.core\b"),
        ],
    ),
    (
        OdooVersion.V16,
        [
            re.compile(r"""['"]version['"]\s*:\s*['"]16\.0"""),
            re.compile(r"from\s+odoo\.cli\.command\b"),
            re.compile(r"Command\b"),
        ],
    ),
    (
        OdooVersion.V15,
        [
            re.compile(r"""['"]version['"]\s*:\s*['"]15\.0"""),
            re.compile(r"from\s+odoo\s+import\s+.*\bfields\b"),
            re.compile(r"from\s+odoo\s+import\s+.*\bmodels\b"),
        ],
    ),
]


def detect_version(code: str, filename: str = "") -> OdooVersion:
    """Detect the Odoo version from source code.

    Strategy:
      1. Check for explicit version strings in __manifest__.py style dicts.
      2. Match version-specific import patterns.
      3. Fall back based on general patterns.

    Args:
        code: The raw source code to analyse.
        filename: The original filename (helps with context).

    Returns:
        The detected OdooVersion.

    Raises:
        VersionDetectionError: If no version can be determined.
    """
    if not code or not code.strip():
        raise VersionDetectionError("Cannot detect version from empty code")

    # Score each version by how many patterns match
    scores: dict[OdooVersion, int] = {v: 0 for v in OdooVersion}

    for version, patterns in _VERSION_PATTERNS:
        for pat in patterns:
            if pat.search(code):
                scores[version] += 1

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] == 0:
        raise VersionDetectionError(
            "Could not detect Odoo version from code"
            + (f" in {filename}" if filename else "")
        )

    return best
