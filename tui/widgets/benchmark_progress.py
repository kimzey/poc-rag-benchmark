"""BenchmarkProgress widget — RichLog output + cancel for benchmark subprocesses."""
from __future__ import annotations

import asyncio
import os
import re
import signal
import subprocess
from enum import Enum, auto

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]|\r")

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog


class BenchmarkState(Enum):
    IDLE = auto()
    RUNNING = auto()
    DONE = auto()
    ERROR = auto()
    CANCELLED = auto()


class BenchmarkProgress(Widget):
    """Real-time log + cancel button for a long-running benchmark subprocess."""

    DEFAULT_CSS = ""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._proc: asyncio.subprocess.Process | None = None
        self._state = BenchmarkState.IDLE

    def compose(self) -> ComposeResult:
        with Horizontal(id="bp-header"):
            yield Label("Idle", id="bp-state")
            yield Button("Cancel", id="bp-cancel", variant="error", disabled=True)
        yield RichLog(id="bp-log", highlight=True, markup=True, wrap=True)

    # ── public API ────────────────────────────────────────────────────────────

    def run_command(self, cmd: list[str], cwd: str | None = None) -> None:
        """Start a benchmark command. Cancels any in-progress run first."""
        if self._state == BenchmarkState.RUNNING:
            self._cancel()
        self.query_one("#bp-log", RichLog).clear()
        self._set_state(BenchmarkState.RUNNING)
        self._stream_subprocess(cmd, cwd)

    def cancel(self) -> None:
        self._cancel()

    # ── internals ─────────────────────────────────────────────────────────────

    def _set_state(self, state: BenchmarkState) -> None:
        self._state = state
        labels = {
            BenchmarkState.IDLE: "[dim]Idle[/dim]",
            BenchmarkState.RUNNING: "[yellow]● Running…[/yellow]",
            BenchmarkState.DONE: "[green]✓ Done[/green]",
            BenchmarkState.ERROR: "[red]✗ Error[/red]",
            BenchmarkState.CANCELLED: "[orange1]⊘ Cancelled[/orange1]",
        }
        self.query_one("#bp-state", Label).update(labels[state])
        is_running = state == BenchmarkState.RUNNING
        self.query_one("#bp-cancel", Button).disabled = not is_running

    def _cancel(self) -> None:
        if self._proc and self._proc.returncode is None:
            try:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                self._proc.terminate()
        self._set_state(BenchmarkState.CANCELLED)

    @work(thread=True)
    def _stream_subprocess(self, cmd: list[str], cwd: str | None) -> None:
        """Run subprocess and stream output line-by-line into RichLog."""
        env = {**os.environ, "FORCE_COLOR": "0", "NO_COLOR": "1"}
        log = self.app.call_from_thread(self.query_one, "#bp-log", RichLog)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )
            # stash pid so cancel() can reach it
            self._proc = proc  # type: ignore[assignment]

            for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
                stripped = _ANSI_RE.sub("", line).rstrip()
                if stripped:
                    self.app.call_from_thread(log.write, stripped)

            proc.wait()
            if self._state == BenchmarkState.RUNNING:
                if proc.returncode == 0:
                    self.app.call_from_thread(self._set_state, BenchmarkState.DONE)
                    self.app.call_from_thread(log.write, "[green]── finished ──[/green]")
                else:
                    self.app.call_from_thread(self._set_state, BenchmarkState.ERROR)
                    self.app.call_from_thread(
                        log.write, f"[red]── exit code {proc.returncode} ──[/red]"
                    )
        except Exception as exc:
            self.app.call_from_thread(self._set_state, BenchmarkState.ERROR)
            self.app.call_from_thread(log.write, f"[red]Error: {exc}[/red]")

    # ── events ────────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "bp-cancel":
            event.stop()
            self._cancel()
