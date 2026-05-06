#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          OMA Agent — Proof of Concept Runner                 ║
║  Brain-powered Odoo migration: real GitHub code as context   ║
╚══════════════════════════════════════════════════════════════╝

Usage (from project root):
    python poc/run_poc.py
    python poc/run_poc.py --file poc/samples/fiscal_year_views.xml --version 15.0 --target 18.0
    python poc/run_poc.py --file poc/samples/fiscal_year_model.py  --version 15.0 --target 19.0
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

# ── Make sure backend package is importable ────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint

console = Console()

# ── Lazy imports (after sys.path fix) ─────────────────────────────
from backend.odoo_brain import fetch_brain_context, format_brain_context
from backend.openrouter_client import llm
from backend.prompt_builder import build_migration_prompt

# ── Supported versions ─────────────────────────────────────────────
VALID_VERSIONS = ["15.0", "16.0", "17.0", "18.0", "19.0"]

# ── Sample files shipped with the POC ─────────────────────────────
SAMPLES = {
    "1": ("poc/samples/fiscal_year_views.xml",  "15.0", "XML — fiscal year tree view"),
    "2": ("poc/samples/fiscal_year_model.py",   "15.0", "Python — fiscal year model"),
}


# ═══════════════════════════════════════════════════════════════════
# Core POC logic
# ═══════════════════════════════════════════════════════════════════

async def run_migration_poc(
    code: str,
    filename: str,
    source_version: str,
    target_version: str,
    incremental: bool = False,
) -> None:
    """
    Full POC pipeline:
      1. Fetch real Odoo GitHub snippets (brain)
      2. Build LLM prompt with brain context injected
      3. Call LLM and show migrated output
      4. Print a rich before/after diff summary
    """

    console.print()
    console.print(Rule("[bold cyan]OMA Agent — Brain-Powered Migration POC[/bold cyan]"))
    console.print()

    # ── Step 1: Brain fetch ────────────────────────────────────────
    brain_context_str: str | None = None
    brain_info: str = "[red]unavailable (GitHub unreachable)[/red]"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"[cyan]🧠  Brain fetching real Odoo {source_version} + {target_version} reference code from GitHub...",
            total=None,
        )
        t0 = time.perf_counter()
        try:
            brain = await fetch_brain_context(
                source_version=source_version,
                target_version=target_version,
                filename=filename,
            )
            if brain:
                brain_context_str = format_brain_context(brain)
                elapsed = time.perf_counter() - t0
                brain_info = (
                    f"[green]✓[/green] {len(brain.source_snippets)} source + "
                    f"{len(brain.target_snippets)} target snippets loaded "
                    f"([dim]{elapsed:.1f}s[/dim])"
                )
        except Exception as e:
            brain_info = f"[yellow]⚠ Brain skipped: {e}[/yellow]"
        finally:
            progress.remove_task(task)

    console.print(f"  🧠  Brain   : {brain_info}")

    # ── Step 2: Build prompt ───────────────────────────────────────
    messages = build_migration_prompt(
        source_version=source_version,
        target_version=target_version,
        filename=filename,
        code=code,
        brain_context=brain_context_str,
    )

    prompt_chars = sum(len(m["content"]) for m in messages)
    console.print(
        f"  📝  Prompt  : [dim]{len(messages)} messages, "
        f"~{prompt_chars:,} chars "
        f"({'with' if brain_context_str else 'WITHOUT'} brain context)[/dim]"
    )

    # ── Step 3: LLM call ──────────────────────────────────────────
    migrated_code: str = ""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            "[magenta]🤖  LLM migrating code to Odoo 19...",
            total=None,
        )
        t1 = time.perf_counter()
        try:
            migrated_code = await llm.chat_completion(messages, temperature=0.1)
        except Exception as e:
            console.print(f"\n[red]✗ LLM call failed: {e}[/red]")
            return
        finally:
            progress.remove_task(task)

    llm_time = time.perf_counter() - t1
    console.print(f"  🤖  LLM     : [green]✓[/green] response in [dim]{llm_time:.1f}s[/dim]")
    console.print()

    # ── Step 4: Display results ────────────────────────────────────
    ext = Path(filename).suffix.lower()
    lang = "xml" if ext == ".xml" else "python" if ext == ".py" else "javascript"

    console.print(Rule("[bold yellow]ORIGINAL CODE[/bold yellow]"))
    console.print(Syntax(code, lang, theme="monokai", line_numbers=True))
    console.print()

    console.print(Rule(f"[bold green]MIGRATED CODE  (Odoo {target_version})[/bold green]"))
    console.print(Syntax(migrated_code, lang, theme="monokai", line_numbers=True))
    console.print()

    # ── Step 5: Quick stats table ──────────────────────────────────
    orig_lines  = code.count("\n") + 1
    migr_lines  = migrated_code.count("\n") + 1
    line_delta  = migr_lines - orig_lines

    table = Table(title="Migration Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric",         style="dim",   width=28)
    table.add_column("Value",          style="white")

    table.add_row("Source version",    source_version)
    table.add_row("Target version",    target_version)
    table.add_row("File",              filename)
    table.add_row("Brain context",     "Yes ✓" if brain_context_str else "No (GitHub unreachable)")
    table.add_row("Original lines",    str(orig_lines))
    table.add_row("Migrated lines",    str(migr_lines))
    table.add_row("Line delta",        f"{'+' if line_delta >= 0 else ''}{line_delta}")
    table.add_row("LLM response time", f"{llm_time:.1f}s")

    console.print(table)
    console.print()

    # ── Save output ────────────────────────────────────────────────
    out_stem = Path(filename).stem
    out_path = PROJECT_ROOT / "poc" / "output" / f"{out_stem}_v{target_version}{Path(filename).suffix}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(migrated_code, encoding="utf-8")
    console.print(
        Panel(
            f"[green]✓[/green] Migrated file saved to:\n[cyan]{out_path}[/cyan]",
            title="Output",
            border_style="green",
        )
    )


# ═══════════════════════════════════════════════════════════════════
# Interactive menu
# ═══════════════════════════════════════════════════════════════════

def pick_sample_interactive() -> tuple[str, str, str, str, bool]:
    """Show an interactive menu and return (code, filename, source_version, target_version, incremental)."""
    console.print()
    console.print(Panel(
        "[bold cyan]OMA Agent — Proof of Concept[/bold cyan]\n"
        "[dim]Brain-powered Odoo migration using real GitHub source as context[/dim]",
        border_style="cyan",
    ))
    console.print()
    console.print("[bold]Select a sample to migrate:[/bold]")
    console.print()

    for key, (path, version, desc) in SAMPLES.items():
        console.print(f"  [cyan]{key}[/cyan]  {desc}  [dim](v{version})[/dim]")

    console.print(f"  [cyan]c[/cyan]  Paste your own code")
    console.print()

    choice = console.input("[bold]Enter choice[/bold] [dim][1/2/c][/dim]: ").strip().lower()

    if choice in SAMPLES:
        rel_path, version, _ = SAMPLES[choice]
        file_path = PROJECT_ROOT / rel_path
        code = file_path.read_text(encoding="utf-8")
        
        target = console.input(f"Target Odoo version {VALID_VERSIONS} (default 19.0): ").strip() or "19.0"
        incr = console.input("Use incremental step-by-step migration? [y/N]: ").strip().lower() == "y"
        return code, file_path.name, version, target, incr

    elif choice == "c":
        console.print()
        filename = console.input("Filename (e.g. models.py or views.xml): ").strip() or "custom.py"
        version  = console.input(f"Source Odoo version {VALID_VERSIONS}: ").strip() or "15.0"
        target = console.input(f"Target Odoo version {VALID_VERSIONS} (default 19.0): ").strip() or "19.0"
        incr = console.input("Use incremental step-by-step migration? [y/N]: ").strip().lower() == "y"
        console.print("[dim]Paste your code below. Enter a line with only '---END---' when done:[/dim]")
        lines = []
        while True:
            line = input()
            if line.strip() == "---END---":
                break
            lines.append(line)
        return "\n".join(lines), filename, version, target, incr

    else:
        console.print("[red]Invalid choice. Exiting.[/red]")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OMA Agent POC — migrate Odoo code using the agent brain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python poc/run_poc.py
  python poc/run_poc.py --file poc/samples/fiscal_year_views.xml --version 15.0 --target 18.0
  python poc/run_poc.py --file poc/samples/fiscal_year_model.py  --version 15.0 --target 19.0 --incremental
        """,
    )
    parser.add_argument("--file",    help="Path to the Odoo source file to migrate")
    parser.add_argument("--version", help="Source Odoo version (e.g. 15.0)", default="15.0")
    parser.add_argument("--target",  help="Target Odoo version (e.g. 19.0)", default="19.0")
    parser.add_argument("--incremental", action="store_true", help="Run incremental step-by-step migration")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            sys.exit(1)
        code     = file_path.read_text(encoding="utf-8")
        filename = file_path.name
        version  = args.version
        target   = args.target
        incr     = args.incremental
    else:
        code, filename, version, target, incr = pick_sample_interactive()

    await run_migration_poc(
        code=code, 
        filename=filename, 
        source_version=version, 
        target_version=target, 
        incremental=incr
    )


if __name__ == "__main__":
    asyncio.run(main())
