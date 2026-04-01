"""Tests screen — run integration tests and stream pytest output."""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog, Rule, Static


_ROOT = Path(__file__).parents[2]


class TestsPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Integration Tests", id="tests-title")
        with Vertical(id="tests-body"):
            with Horizontal(id="tests-controls"):
                yield Button("▶  Run All Tests", id="tests-btn-run", variant="primary")
                yield Button("Clear", id="tests-btn-clear")
                yield Static("", id="tests-status")
            yield Static(
                "[dim]Runs: uv run pytest tests/integration/ -v --tb=short[/dim]",
                id="tests-hint",
            )
            yield Rule()
            yield RichLog(id="tests-log", highlight=True, markup=True)
            yield Static("", id="tests-summary")

    # ── controls ──────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#tests-btn-run")
    def on_run(self) -> None:
        self._run_tests()

    @on(Button.Pressed, "#tests-btn-clear")
    def on_clear(self) -> None:
        self.query_one("#tests-log", RichLog).clear()
        self.query_one("#tests-summary", Static).update("")
        self.query_one("#tests-status", Static).update("")

    # ── test runner ───────────────────────────────────────────────────────────

    @work(exclusive=True)
    async def _run_tests(self) -> None:
        log = self.query_one("#tests-log", RichLog)
        status = self.query_one("#tests-status", Static)
        summary = self.query_one("#tests-summary", Static)
        run_btn = self.query_one("#tests-btn-run", Button)

        log.clear()
        summary.update("")
        status.update("[dim]Running…[/dim]")
        run_btn.disabled = True

        cmd = [
            "uv", "run", "pytest", "tests/integration/",
            "-v", "--tb=short", "--no-header",
        ]

        passed = failed = 0
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(_ROOT),
            )

            assert proc.stdout is not None
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").rstrip()

                if " PASSED" in line:
                    passed += 1
                    log.write(f"[green]{line}[/green]")
                elif " FAILED" in line or " ERROR" in line:
                    failed += 1
                    log.write(f"[red]{line}[/red]")
                elif line.startswith("FAILED ") or line.startswith("ERROR "):
                    log.write(f"[red]{line}[/red]")
                elif line.startswith("===") or line.startswith("---"):
                    log.write(f"[bold]{line}[/bold]")
                else:
                    log.write(line)

            await proc.wait()
            rc = proc.returncode
            color = "green" if failed == 0 and rc == 0 else "red"
            summary.update(
                f"[{color}]{'✓' if color == 'green' else '✗'}  "
                f"{passed} passed / {failed} failed  (exit {rc})[/{color}]"
            )
            status.update(f"[dim]Done[/dim]")

        except FileNotFoundError:
            log.write("[red]Error: 'uv' not found — run from project root[/red]")
            status.update("[red]Error[/red]")
        except Exception as exc:
            log.write(f"[red]Error: {exc}[/red]")
            status.update(f"[red]{exc}[/red]")
        finally:
            run_btn.disabled = False
