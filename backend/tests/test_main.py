"""
Tests for backend.main (Module 13) — FastAPI endpoints
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Root Endpoint ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_root_returns_app_info(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app"] == "OMA Agent"
    assert "version" in data
    assert data["docs"] == "/docs"


# ── Health Endpoint ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── OpenAPI Schema ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_openapi_schema_available(client):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "OMA Agent"
    assert "/health" in schema["paths"]


# ── CORS Headers ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cors_headers(client):
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


# ── 404 for unknown routes ───────────────────────────────────────
@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
