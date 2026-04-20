# Changelog

This document tracks all implemented changes and improvements to the project.

## Improvements Added
- **Testing Structure**: Configured Vitest and React Testing Library for the frontend components. Added tests for API client and layout elements. Passed all tests using `happy-dom` testing environment.
- **Frontend Core Components**: Implemented `CodeEditor.tsx`, `MigrationResults.tsx`, `ChatInterface.tsx` and main dashboard `App.tsx` utilizing `@monaco-editor/react`. (Completed modules 16-20)
- **Backend Readiness**: Finished modules 03-12 for processing migrations, analyzing AST trees, detecting common structural issues, parsing diffs, and formatting AI contexts. All endpoints operational.
- **Report Page (Module 21)**: Added `ReportPage.tsx` component with JSON/Text export support, integrated into `App.tsx` as a third tab.
- **Type Alignment Fix**: Aligned frontend `api.ts` types with backend `schemas.py` — fixed `line_number`→`line`, `fix_hint`→`suggestion`, `ChatResponse.message`→`reply`, and updated `ChatRequest` to use `message`/`context` instead of `messages` array.
- **App.tsx Import Fix**: Moved misplaced `AlertTriangle`/`Download` imports from bottom of file to top-level import statement.
- **Frontend Tests (Module 22)**: Added `ReportPage.test.tsx` (3 tests), `api.report()` test, updated all existing tests to match corrected types. Total: 12 frontend tests passing.
- **Integration Tests (Module 23)**: Created `test_integration.py` with 6 end-to-end tests covering migrate→report flow (JSON + text), chat flow, error handling (invalid version, empty message), and health/root endpoints.
- **Docker Compose (Module 24)**: Added `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, and `docker-compose.yml` for single-command full-stack deployment.

## Project Completion Sprint (2026-04-16)

- **Advanced SQL Pattern Analysis**: `code_analyzer.py` now detects `cr.execute`, `self.env.cr.execute`, `self._cr.execute`, and inline SQL strings (SELECT/INSERT/UPDATE/DELETE/etc.) with exact line number reporting. `has_raw_sql` and `raw_sql_lines` added to `AnalysisResult` and `to_dict()`. Two new issue check rules added to `issue_detector.py`. 10 new backend tests in `test_sql_detection.py` — all passing.
- **Enhanced LLM Prompts**: `prompt_builder.py` fully rewritten with per-version migration context maps (v15/v16/v17/v18 → v19), a shared `_ODOO19_GENERAL_RULES` block applied to all prompts, and a new `build_apply_fix_prompt` for minimal targeted patches at temperature 0.1.
- **Multi-file Migration API**: Added `FileItem`, `MultiFileMigrationRequest`, `MultiFileMigrationResponse`, `MultiFileMigrationResult` schemas. `POST /api/migrate/multi` endpoint runs all module files concurrently via `asyncio.gather`, skipping unsupported extensions.
- **Interactive Fix API**: Added `ApplyFixRequest`/`ApplyFixResponse` schemas and `POST /api/apply_fix` endpoint. `run_apply_fix()` in `agent_pipeline.py` uses LLM at temperature 0.1 to apply the minimally-scoped fix from a suggestion string.
- **File Upload Component**: New `FileUpload.tsx` with full drag-and-drop support, multi-extension filtering (.py/.xml/.js/.ts/.csv/.json), 2MB per-file limit, uploaded file list with remove buttons, and per-extension colour coding.
- **App.tsx Multi-file UI**: Upload toggle drawer, file tab pills showing per-file issue counts, "Migrate All" button for batch runs, prev/next file navigation arrows in the results pane, and unified `displayResult` that works in both single and multi-file mode.
- **MigrationResults.tsx Interactive Fixes**: IssueCards now include an "Apply Fix" button per issue. On click, calls `/api/apply_fix`, receives patched code, and propagates to the editor via the `onCodePatched` callback. Collapsible AI explanation panel added.
- **Playwright E2E Tests**: 13 end-to-end tests in `frontend/e2e/migration.spec.ts` covering: page load, UI inputs, version dropdown, upload panel toggle, file drop simulation, mocked migration flow, spinner state, issues list visibility, apply-fix button, report tab gating, and error banner.
- **Full Regression**: All 74 backend pytest tests continue to pass after all changes.
