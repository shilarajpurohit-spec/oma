.PHONY: run test install lint clean help

# ── Default ───────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  OMA Agent — available commands"
	@echo ""
	@echo "  make install   Install Python dependencies"
	@echo "  make run       Start the FastAPI backend (dev mode)"
	@echo "  make test      Run all tests with coverage"
	@echo "  make lint      Run ruff linter"
	@echo "  make clean     Remove cache and build files"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# ── Run ───────────────────────────────────────────────────────────
run:
	venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# ── Test ──────────────────────────────────────────────────────────
test:
	venv/bin/pytest backend/tests/ -v --cov=backend --cov-report=term-missing

test-module:
	venv/bin/pytest backend/tests/$(module) -v

# ── Lint ──────────────────────────────────────────────────────────
lint:
	venv/bin/ruff check backend/

# ── Clean ─────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type f -name ".coverage" -delete