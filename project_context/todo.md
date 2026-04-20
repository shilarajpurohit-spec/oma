# Future Approach & To-Do

## Completed ✅
- [x] **Report Generation Page (Module 21)**: Built `ReportPage.tsx` with JSON/Text export, integrated as third tab in dashboard.
- [x] **Frontend Integration Tests (Module 23)**: Added backend integration tests via `test_integration.py`.
- [x] **Docker Compose Stack (Module 24)**: Backend + Frontend containers with `docker-compose.yml`.
- [x] **LLM Prompt Adjustments**: Rewrote `prompt_builder.py` with version-specific migration context (v15/16/17/18) and detailed Odoo 19 deprecation rules. Added `build_apply_fix_prompt` for targeted fix application.
- [x] **Advanced Pattern Analysis (SQL)**: `code_analyzer.py` now detects `cr.execute`, `self.env.cr.execute`, `self._cr.execute`, and inline SQL strings; line numbers reported. Added matching issue rules to `issue_detector.py`. 10 dedicated backend tests in `test_sql_detection.py`.
- [x] **Interactive Fixes**: `MigrationResults.tsx` IssueCards now have an "Apply Fix" button that calls `POST /api/apply_fix`, uses LLM to apply targeted minimal patches, and updates the editor via `onCodePatched` callback. Added `ApplyFixRequest/Response` schemas and `run_apply_fix` pipeline function.
- [x] **File Upload Support**: `FileUpload.tsx` component with drag-and-drop, multi-extension support (.py/.xml/.js/.ts/.csv/.json), 2MB limit, per-file colour coding. Single-file populates editor; multi-file queues for batch migration.
- [x] **Multi-file Migration**: `POST /api/migrate/multi` endpoint runs all module files concurrently via `asyncio.gather`. File tab pills in the UI navigate between per-file results with issue counts shown.
- [x] **Cypress/Playwright E2E Tests**: Full Playwright test suite in `frontend/e2e/migration.spec.ts` — 13 tests covering smoke, UI interactions, file upload, mocked migration flow, apply-fix visibility, error banner, and report tab state.

## Possible Future Enhancements
- [ ] **Progress Bar for Multi-file**: Show per-file migration progress with streaming updates via Server-Sent Events.
- [ ] **Diff Export**: Allow downloading a `.patch` file of the unified diff directly from the UI.
- [ ] **Module Registry Check**: Cross-reference migrated module manifest `depends` against known Odoo 19 module names.
- [ ] **Odoo 19 Breaking Changes DB**: Maintain a structured YAML/JSON database of Odoo 19 API breaking changes for deterministic (non-LLM) rule matching.
