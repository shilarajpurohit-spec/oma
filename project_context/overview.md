# OMA Agent — Odoo Migration AI Agent
An agentic AI system that migrates Odoo modules from v15–v18 to Odoo 19. Powered by OpenRouter + DeepSeek R1.

## Stack
- **Backend:** Python 3.11, FastAPI
- **LLM:** DeepSeek R1 via OpenRouter (free)
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS

## Current State
The project is segmented into a FastAPI backend and a React/Vite/Tailwind frontend.
1. **Backend API**: The core OpenRouter integration, Odoo module AST code analyzer, issue detector, rule engine, and FastAPI endpoints are fully implemented and passing all tests.
2. **Frontend Layout**: The main dashboard is designed with a modern aesthetic, containing:
   - `CodeEditor`: Interactive Monaco Editor.
   - `MigrationResults`: Displaying unified diffs via Monaco DiffEditor and parsing severity-based issues.
   - `ChatInterface`: Allowing contextual QA dialog with the LLM.
