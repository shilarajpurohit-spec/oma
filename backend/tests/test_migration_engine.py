"""
Tests for backend.migration_engine (Module 07)
"""

import pytest
from unittest.mock import patch, AsyncMock
from backend.schemas import MigrationRequest, OdooVersion


@pytest.fixture
def sample_request():
    return MigrationRequest(
        module_name="test_mod",
        source_version=OdooVersion.V15,
        filename="test.py",
        file_content="from openerp import models\nclass Test(osv.osv):\n    _name = 'test'\n"
    )


@pytest.mark.asyncio
@patch("backend.migration_engine.llm", new_callable=AsyncMock)
async def test_migrate_code_success(mock_llm, sample_request):
    mock_llm.chat_completion.return_value = "from odoo import models\nclass Test(models.Model):\n    _name = 'test'\n"

    from backend.migration_engine import migrate_code
    
    resp = await migrate_code(sample_request)

    assert resp.original_code == sample_request.file_content
    # The LLM return value should be adopted
    assert "models.Model" in resp.migrated_code
    
    # Pure diff-based migration does not generate static rule-based issues.
    assert resp.issues == []
    
    # Diff should be populated
    assert resp.diff.startswith("--- a/test.py")


@pytest.mark.asyncio
@patch("backend.migration_engine.llm", new_callable=AsyncMock)
async def test_migrate_code_strips_markdown(mock_llm, sample_request):
    mock_llm.chat_completion.return_value = "```python\nfrom odoo import models\n```"
    
    from backend.migration_engine import migrate_code
    
    resp = await migrate_code(sample_request)
    assert resp.migrated_code == "from odoo import models\n"


@pytest.mark.asyncio
@patch("backend.migration_engine.llm", new_callable=AsyncMock)
async def test_migrate_code_llm_failure_fallback(mock_llm, sample_request):
    mock_llm.chat_completion.side_effect = Exception("API down")
    
    from backend.migration_engine import migrate_code
    
    resp = await migrate_code(sample_request)
    
    # When the LLM fails, fallback preserves the original source code.
    assert resp.migrated_code == sample_request.file_content
