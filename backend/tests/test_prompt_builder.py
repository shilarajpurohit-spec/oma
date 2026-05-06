"""
Tests for backend.prompt_builder (Module 11)
"""

from backend.prompt_builder import build_migration_prompt, build_explanation_prompt, build_chat_prompt


def test_build_migration_prompt():
    messages = build_migration_prompt("15.0", "19.0", "models/sale.py", "class SaleOrder:")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "expert Odoo developer" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "15.0" in messages[1]["content"]
    assert "19.0" in messages[1]["content"]
    assert "models/sale.py" in messages[1]["content"]
    assert "class SaleOrder:" in messages[1]["content"]


def test_build_explanation_prompt():
    # Without issues
    messages = build_explanation_prompt("def old(): pass", "def new(): pass")
    assert len(messages) == 2
    assert "old(): pass" in messages[1]["content"]
    assert "new(): pass" in messages[1]["content"]
    assert "Detected issues" not in messages[1]["content"]

    # With issues
    issues = [{"severity": "high", "message": "Deprecated call"}]
    messages_with_issues = build_explanation_prompt("old", "new", issues=issues)
    assert "Detected issues:\n  1. [HIGH] Deprecated call" in messages_with_issues[1]["content"]


def test_build_chat_prompt():
    messages = build_chat_prompt("How do I migrate this?", "def foo(): pass")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "How do I migrate this?" in messages[1]["content"]
    assert "def foo(): pass" in messages[1]["content"]
