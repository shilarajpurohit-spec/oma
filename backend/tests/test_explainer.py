"""
Tests for backend.explainer (Module 09)
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.schemas import MigrationIssue, Severity


@pytest.mark.asyncio
@patch("backend.explainer.llm", new_callable=AsyncMock)
async def test_explain_migration(mock_llm):
    mock_llm.chat_completion.return_value = "Explanation: changed foo to bar."

    from backend.explainer import explain_migration

    issues = [MigrationIssue(line=1, severity=Severity.HIGH, message="test")]
    result = await explain_migration("old", "new", issues)

    assert result == "Explanation: changed foo to bar."
    # ensure it was called
    assert mock_llm.chat_completion.called


@pytest.mark.asyncio
@patch("backend.explainer.llm", new_callable=AsyncMock)
async def test_explain_migration_handles_failure(mock_llm):
    mock_llm.chat_completion.side_effect = Exception("Boom")

    from backend.explainer import explain_migration

    result = await explain_migration("old", "new")
    assert "error" in result.lower()
