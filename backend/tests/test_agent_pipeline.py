"""
Tests for backend.agent_pipeline (Module 10)
"""

import pytest
from unittest.mock import patch, AsyncMock

from backend.schemas import MigrationRequest, OdooVersion, MigrationResponse, ChatRequest


@pytest.fixture
def mock_response():
    return MigrationResponse(
        module_name="test",
        source_version="15.0",
        target_version="19.0",
        original_code="old",
        migrated_code="new",
        diff="",
        issues=[],
        explanation=""
    )


@pytest.mark.asyncio
@patch("backend.agent_pipeline.explain_migration")
@patch("backend.agent_pipeline.migrate_code")
async def test_run_migration(mock_migrate, mock_explain, mock_response):
    mock_migrate.return_value = mock_response
    mock_explain.return_value = "Detailed explanation."
    
    from backend.agent_pipeline import run_migration
    
    req = MigrationRequest(
        module_name="test",
        source_version=OdooVersion.V15,
        file_content="from openerp import models",
        filename="test.py"
    )
    
    result = await run_migration(req)
    
    assert mock_migrate.called
    assert mock_explain.called
    assert result.explanation == "Detailed explanation."


@pytest.mark.asyncio
@patch("backend.agent_pipeline.llm", new_callable=AsyncMock)
async def test_run_chat(mock_llm):
    mock_llm.chat_completion.return_value = "I am OMA Agent."
    
    from backend.agent_pipeline import run_chat
    
    req = ChatRequest(message="Who are you?")
    result = await run_chat(req)
    
    assert result.reply == "I am OMA Agent."
    assert mock_llm.chat_completion.called
