"""
Tests for endpoints added to main.py (Module 15 API)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from backend.main import app
from backend.schemas import MigrationResponse, ChatResponse


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@patch("backend.main.run_migration")
async def test_api_migrate(mock_run, client):
    mock_run.return_value = MigrationResponse(
        module_name="test",
        source_version="15.0",
        target_version="19.0",
        original_code="old",
        migrated_code="new"
    )
    
    resp = await client.post("/api/migrate", json={
        "module_name": "test",
        "source_version": "15.0",
        "target_version": "19.0",
        "file_content": "old",
        "filename": "test.py",
        "incremental": False
    })
    
    assert resp.status_code == 200
    assert resp.json()["migrated_code"] == "new"


@pytest.mark.asyncio
@patch("backend.main.run_chat")
async def test_api_chat(mock_run, client):
    mock_run.return_value = ChatResponse(reply="hello")
    
    resp = await client.post("/api/chat", json={
        "message": "Hi"
    })
    
    assert resp.status_code == 200
    assert resp.json()["reply"] == "hello"


@pytest.mark.asyncio
async def test_api_report_json(client):
    # Tests the report endpoint locally
    payload = {
        "response": {
            "module_name": "test",
            "source_version": "15.0",
            "original_code": "o",
            "migrated_code": "m",
            "target_version": "19.0",
            "diff": "",
            "issues": [],
            "explanation": ""
        },
        "format": "json"
    }
    
    resp = await client.post("/api/report", json=payload)
    assert resp.status_code == 200
    assert "test" in resp.json()  # json response


@pytest.mark.asyncio
async def test_api_report_text(client):
    payload = {
        "response": {
            "module_name": "test",
            "source_version": "15.0",
            "original_code": "o",
            "migrated_code": "m",
            "target_version": "19.0",
            "diff": "",
            "issues": [],
            "explanation": "Summary."
        },
        "format": "text"
    }
    
    resp = await client.post("/api/report", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "Summary." in resp.text
