"""
OMA Agent — Report Generator (Module 12)
Generate migration reports in text or JSON formats.
"""

from __future__ import annotations

from datetime import datetime

from jinja2 import Template

from backend.schemas import MigrationResponse

_TEXT_TEMPLATE = """
================================================================================
OMA Agent Migration Report
================================================================================
Generated: {{ date }}

Module: {{ module_name }}
Source Version: {{ source_version }}
Target Version: {{ target_version }}

--------------------------------------------------------------------------------
1. Summary & Explanation
--------------------------------------------------------------------------------
{{ explanation }}

--------------------------------------------------------------------------------
2. Detected Issues ({{ issues|length }})
--------------------------------------------------------------------------------
{% for issue in issues %}
[{{ issue.severity|upper }}] Line {{ issue.line }}: {{ issue.message }}
  -> Suggestion: {{ issue.suggestion }}
{% else %}
No issues detected.
{% endfor %}

--------------------------------------------------------------------------------
3. Code Diff
--------------------------------------------------------------------------------
{{ diff }}
"""


def generate_report(response: MigrationResponse, format: str = "json") -> str:
    """Generate a final report of the migration.

    Args:
        response: The fully populated MigrationResponse.
        format: 'json' or 'text'.

    Returns:
        The formatted report string.
    """
    if format.lower() == "json":
        return response.model_dump_json(indent=2)
    
    # Text format
    template = Template(_TEXT_TEMPLATE.strip())
    
    data = response.model_dump()
    data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return template.render(**data)
