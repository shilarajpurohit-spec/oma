"""
OMA Agent — FastAPI Application (Module 13)
Main entry point for the backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.schemas import HealthResponse

# ── AI Agent Endpoints schemas & functions ───────────────────────
from backend.schemas import (
    MigrationRequest, MigrationResponse,
    MultiFileMigrationRequest, MultiFileMigrationResponse,
    ChatRequest, ChatResponse,
    ReportRequest,
    ApplyFixRequest, ApplyFixResponse,
    VersionDetectRequest, VersionDetectResponse,
)
from backend.agent_pipeline import run_migration, run_multi_migration, run_chat, run_apply_fix
from backend.version_detector import detect_version, VersionDetectionError
from backend.report_gen import generate_report
from fastapi.responses import PlainTextResponse

# ── App instance ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="AI-powered Odoo module migration agent (v15-v18 → v19)",
)

# ── CORS (allow React dev server) ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Returns the application health status."""
    return HealthResponse(status="ok", version=settings.app_version)


@app.get("/", tags=["system"])
async def root():
    """Root endpoint — redirects to docs."""
    return {
        "app": settings.app_title,
        "version": settings.app_version,
        "docs": "/docs",
    }


# ── AI Agent Endpoints ────────────────────────────────────────────

@app.post("/api/migrate", response_model=MigrationResponse, tags=["migration"])
async def api_migrate(request: MigrationRequest):
    """Run the Odoo module migration pipeline."""
    return await run_migration(request)


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def api_chat(request: ChatRequest):
    """Send a message to the AI assistant."""
    return await run_chat(request)


@app.post("/api/report", tags=["reports"])
async def api_report(request: ReportRequest):
    """Generate a migration report in JSON or plain text format."""
    report_text = generate_report(request.response, request.format)

    if request.format.lower() == "text":
        return PlainTextResponse(report_text)
    return report_text  # returns json


@app.post("/api/migrate/multi", response_model=MultiFileMigrationResponse, tags=["migration"])
async def api_migrate_multi(request: MultiFileMigrationRequest):
    """Migrate all files in an Odoo module simultaneously."""
    return await run_multi_migration(request)


@app.post("/api/apply_fix", response_model=ApplyFixResponse, tags=["migration"])
async def api_apply_fix(request: ApplyFixRequest):
    """Apply a targeted fix to source code using the LLM."""
    return await run_apply_fix(request)


@app.post("/api/detect-version", response_model=VersionDetectResponse, tags=["system"])
async def api_detect_version(request: VersionDetectRequest):
    """Attempt to detect Odoo version from source code."""
    try:
        version = detect_version(request.code, request.filename)
        return VersionDetectResponse(version=version)
    except VersionDetectionError:
        return VersionDetectResponse(version="15.0")  # Default if unknown
