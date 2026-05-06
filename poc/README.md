# OMA Agent — Proof of Concept

A standalone CLI demonstrating the **brain-powered** Odoo migration pipeline.

Instead of hardcoded rules, the agent fetches **real Odoo source code from GitHub**
for both the source version and the latest reference version, injects them as
few-shot examples into the LLM prompt, and produces a highly accurate migration.

---

## What it demonstrates

| Step | What happens |
|------|-------------|
| 🧠 **Brain fetch** | Downloads real Odoo view/model files from `github.com/odoo/odoo` |
| 🔀 **Before/After** | Shows source-version code alongside target-version (v18) code |
| 🤖 **LLM migration** | Prompt includes real examples → LLM mirrors them exactly |
| 💾 **Output saved** | Migrated file written to `poc/output/` |

---

## Quick start

```bash
# From the project root
cd /home/shila/oma-agent

# Run interactive menu
python poc/run_poc.py

# Or pass a file directly
python poc/run_poc.py --file poc/samples/fiscal_year_views.xml --version 15.0
python poc/run_poc.py --file poc/samples/fiscal_year_model.py  --version 15.0

# Your own file
python poc/run_poc.py --file path/to/my_module/views.xml --version 16.0
```

---

## Sample files

| File | Version | What it shows |
|------|---------|---------------|
| `samples/fiscal_year_views.xml` | 15.0 | `<tree>` → `<list>` migration + `view_type` removal |
| `samples/fiscal_year_model.py`  | 15.0 | `openerp` imports, `api.multi`, `api.one`, `self.pool`, `sudo(user)` |

---

## Output

Migrated files are saved to `poc/output/` with `_v19` appended to the filename.

---

## How the brain works

```
User code (v15 XML)
        │
        ▼
┌───────────────────┐
│   odoo_brain.py   │  ◄─ fetches same file from GitHub (v15 branch + v18 branch)
│                   │     caches to .odoo_brain_cache/ for 24h
│  source snippets  │  = "old style" examples
│  target snippets  │  = "new style" examples  (v18 as target reference)
└────────┬──────────┘
         │ brain_context injected into system prompt
         ▼
┌───────────────────┐
│  prompt_builder   │  system prompt = rules + REAL CODE EXAMPLES
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   LLM (OpenRouter)│  sees real before/after → mirrors new style exactly
└────────┬──────────┘
         │
         ▼
   Migrated code (v19)
```

---

## Prerequisites

The POC reuses the project's `.env` and `venv`:

```
OPENROUTER_API_KEY=your-key-here
```

No extra dependencies needed — everything is already in `requirements.txt`.
