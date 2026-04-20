"""
OMA Agent — Integration Tests (Module 23)
End-to-end flows through the full pipeline via the FastAPI TestClient.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, AsyncMock

from backend.main import app
from backend.schemas import MigrationResponse


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Full Migration → Report Flow ─────────────────────────────────────

MOCK_MIGRATION_RESPONSE = MigrationResponse(
    module_name="sale_custom",
    source_version="15.0",
    target_version="19.0",
    original_code="from odoo.osv import fields",
    migrated_code="from odoo import fields",
    diff="- from odoo.osv import fields\n+ from odoo import fields",
    issues=[
        {
            "line": 1,
            "severity": "high",
            "message": "odoo.osv is removed in v19",
            "suggestion": "Use odoo.fields instead",
        }
    ],
    explanation="Replaced deprecated odoo.osv imports with modern odoo imports.",
)


@pytest.mark.asyncio
@patch("backend.main.run_migration")
async def test_migrate_then_report_json(mock_run_migration, client):
    """Integration test: migrate code, then generate a JSON report from the result."""
    mock_run_migration.return_value = MOCK_MIGRATION_RESPONSE

    # Step 1: Call migrate
    migrate_resp = await client.post("/api/migrate", json={
        "module_name": "sale_custom",
        "source_version": "15.0",
        "file_content": "from odoo.osv import fields",
        "filename": "models/sale.py",
    })

    assert migrate_resp.status_code == 200
    migration_data = migrate_resp.json()
    assert migration_data["module_name"] == "sale_custom"
    assert migration_data["migrated_code"] == "from odoo import fields"
    assert len(migration_data["issues"]) == 1
    assert migration_data["issues"][0]["severity"] == "high"

    # Step 2: Generate report from migration result
    report_resp = await client.post("/api/report", json={
        "response": migration_data,
        "format": "json",
    })

    assert report_resp.status_code == 200
    report_text = report_resp.text
    assert "sale_custom" in report_text
    assert "19.0" in report_text


@pytest.mark.asyncio
@patch("backend.main.run_migration")
async def test_migrate_then_report_text(mock_run_migration, client):
    """Integration test: migrate code, then generate a text report."""
    mock_run_migration.return_value = MOCK_MIGRATION_RESPONSE

    # Step 1: Migrate
    migrate_resp = await client.post("/api/migrate", json={
        "module_name": "sale_custom",
        "source_version": "15.0",
        "file_content": "from odoo.osv import fields",
        "filename": "models/sale.py",
    })
    assert migrate_resp.status_code == 200
    migration_data = migrate_resp.json()

    # Step 2: Text report
    report_resp = await client.post("/api/report", json={
        "response": migration_data,
        "format": "text",
    })
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"].startswith("text/plain")
    assert "sale_custom" in report_resp.text
    assert "odoo.osv is removed" in report_resp.text


# ── Chat Flow ────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("backend.main.run_chat")
async def test_chat_flow(mock_run_chat, client):
    """Integration test: send a chat message and receive an assistant reply."""
    from backend.schemas import ChatResponse

    mock_run_chat.return_value = ChatResponse(
        reply="The `fields.Many2one` API remains compatible in v19.",
        tokens_used=42,
    )

    resp = await client.post("/api/chat", json={
        "message": "Is fields.Many2one still available in Odoo 19?",
        "context": "from odoo import fields",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "Many2one" in data["reply"]
    assert data["tokens_used"] == 42


# ── Error Handling ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_migrate_invalid_version(client):
    """Should return 422 for an invalid source version."""
    resp = await client.post("/api/migrate", json={
        "module_name": "test",
        "source_version": "99.0",
        "file_content": "pass",
        "filename": "test.py",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_empty_message(client):
    """Should return 422 for an empty chat message."""
    resp = await client.post("/api/chat", json={
        "message": "",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_and_root_integration(client):
    """Smoke test that health and root endpoints are reachable."""
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    root = await client.get("/")
    assert root.status_code == 200
    assert "OMA" in root.json()["app"]
