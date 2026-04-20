"""
OMA Agent — Code Analyzer (Module 05)
AST + pattern-based scanner for Odoo Python modules.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Structured output of code analysis."""

    classes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    fields: list[dict[str, str]] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    model_names: list[str] = field(default_factory=list)
    has_onchange: bool = False
    has_compute: bool = False
    has_constrains: bool = False
    has_api_depends: bool = False
    has_inherit: bool = False
    has_raw_sql: bool = False
    raw_sql_lines: list[int] = field(default_factory=list)
    line_count: int = 0

    def to_dict(self) -> dict:
        """Serialise to a plain dict."""
        return {
            "classes": self.classes,
            "methods": self.methods,
            "imports": self.imports,
            "fields": self.fields,
            "decorators": self.decorators,
            "model_names": self.model_names,
            "has_onchange": self.has_onchange,
            "has_compute": self.has_compute,
            "has_constrains": self.has_constrains,
            "has_api_depends": self.has_api_depends,
            "has_inherit": self.has_inherit,
            "has_raw_sql": self.has_raw_sql,
            "raw_sql_lines": self.raw_sql_lines,
            "line_count": self.line_count,
        }


# ── Field detection regex ─────────────────────────────────────────
_FIELD_PATTERN = re.compile(
    r"(\w+)\s*=\s*fields\.(Char|Integer|Float|Boolean|Text|Html|Date|Datetime"
    r"|Binary|Selection|Many2one|One2many|Many2many|Monetary|Reference|Image"
    r"|Json)\b"
)

_MODEL_NAME_PATTERN = re.compile(r"""_name\s*=\s*['"]([^'"]+)['"]""")
_INHERIT_PATTERN = re.compile(r"""_inherit\s*=\s*['"\[]""")

# ── Raw SQL detection ──────────────────────────────────────────────
# Matches: self.env.cr.execute(, self._cr.execute(, cr.execute(
_RAW_SQL_EXECUTE_PATTERN = re.compile(
    r"\b(?:self\.env\.cr|self\._cr|(?<!\.)(cr))\s*\.\s*execute\s*\("
)
# Matches inline SQL strings containing SELECT/INSERT/UPDATE/DELETE
_INLINE_SQL_PATTERN = re.compile(
    r"(?:'\"|\"\"\"|\'\'\'|f?['\"])\s*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+",
    re.IGNORECASE,
)


def analyze_code(code: str, filename: str = "") -> AnalysisResult:
    """Analyse Odoo Python source code.

    Uses the ``ast`` module for structural extraction and regex for
    Odoo-specific patterns.

    Args:
        code: Raw Python source code.
        filename: Original filename (for error context).

    Returns:
        A populated AnalysisResult.
    """
    result = AnalysisResult(line_count=code.count("\n") + 1 if code else 0)

    # ── AST pass ──────────────────────────────────────────────────
    try:
        tree = ast.parse(code, filename=filename or "<string>")
    except SyntaxError:
        # Fall back to regex-only analysis for non-parseable files
        _regex_analysis(code, result)
        return result

    for node in ast.walk(tree):
        # Classes
        if isinstance(node, ast.ClassDef):
            result.classes.append(node.name)
            for deco in node.decorator_list:
                result.decorators.append(_decorator_name(deco))

        # Methods / functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.methods.append(node.name)
            for deco in node.decorator_list:
                dname = _decorator_name(deco)
                result.decorators.append(dname)
                if "onchange" in dname:
                    result.has_onchange = True
                if "depends" in dname:
                    result.has_api_depends = True
                if "constrains" in dname:
                    result.has_constrains = True

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result.imports.append(f"{module}.{alias.name}")

    # ── Regex pass (Odoo-specific) ────────────────────────────────
    _regex_analysis(code, result)

    return result


def _regex_analysis(code: str, result: AnalysisResult) -> None:
    """Extract Odoo-specific patterns via regex."""

    # Fields
    for match in _FIELD_PATTERN.finditer(code):
        result.fields.append({
            "name": match.group(1),
            "type": match.group(2),
        })

    # Model names
    for match in _MODEL_NAME_PATTERN.finditer(code):
        result.model_names.append(match.group(1))

    # Inheritance
    if _INHERIT_PATTERN.search(code):
        result.has_inherit = True

    # Compute detection
    if re.search(r"compute\s*=\s*['\"]_compute_", code):
        result.has_compute = True

    # Raw SQL detection (line-by-line for line numbers)
    for line_num, line_text in enumerate(code.splitlines(), 1):
        if _RAW_SQL_EXECUTE_PATTERN.search(line_text) or _INLINE_SQL_PATTERN.search(line_text):
            result.has_raw_sql = True
            result.raw_sql_lines.append(line_num)


def _decorator_name(node: ast.expr) -> str:
    """Extract a human-readable name from a decorator AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_decorator_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return "<unknown>"
