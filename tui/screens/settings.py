"""Settings screen — API URL, env vars, TUI info."""
from __future__ import annotations

import os

import httpx
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Rule, Static

from tui.config import settings as tui_settings


_ENV_KEYS: list[tuple[str, str]] = [
    ("OPENROUTER_API_KEY", "OPENROUTER"),
    ("OPENAI_API_KEY", "OPENAI"),
    ("ANTHROPIC_API_KEY", "ANTHROPIC"),
    ("COHERE_API_KEY", "COHERE"),
    ("LINE_CHANNEL_SECRET", "LINE"),
]


class SettingsPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Settings", id="settings-title")
        with Vertical(id="settings-body"):
            # API connection
            yield Label("API Connection", classes="section-header")
            yield Static("", id="settings-current-url")
            with Horizontal(id="settings-url-row"):
                yield Input(
                    value=tui_settings.api_base_url,
                    placeholder="http://localhost:8000",
                    id="settings-url-input",
                )
                yield Button("Apply & Test", id="settings-btn-apply", variant="primary")
            yield Static("", id="settings-conn-status")
            yield Rule()
            # Environment variables
            yield Label("API Keys (from .env)", classes="section-header")
            yield Static("", id="settings-env-vars")
            yield Rule()
            # TUI info
            yield Label("TUI Info", classes="section-header")
            yield Static("", id="settings-info")

    def on_mount(self) -> None:
        self._refresh()

    def on_show(self) -> None:
        self._refresh()
        self._check_connection()

    def _refresh(self) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        self.query_one("#settings-current-url", Static).update(
            f"Current: [bold]{client.base_url}[/bold]"
        )
        self.query_one("#settings-url-input", Input).value = client.base_url

        lines = [
            f"{'[green]✓[/green]' if os.getenv(env_key) else '[red]✗[/red]'} {label}"
            for env_key, label in _ENV_KEYS
        ]
        self.query_one("#settings-env-vars", Static).update("\n".join(lines))

        user_line = "[dim]Not logged in[/dim]"
        if client.current_user:
            u = client.current_user
            user_line = f"Logged in as [bold]{u['username']}[/bold] ({u['user_type']})"
        self.query_one("#settings-info", Static).update(
            f"{user_line}\n"
            f"Embedded mode: {'Yes' if tui_settings.embedded_mode else 'No'}\n"
            f"TUI version: 0.4.0"
        )

    @work
    async def _check_connection(self) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        connected = await client.health_check()
        self.query_one("#settings-conn-status", Static).update(
            "[green]● Connected[/green]" if connected else "[red]● Disconnected — run: make api-run[/red]"
        )

    # ── apply URL ─────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#settings-btn-apply")
    def on_apply(self) -> None:
        url = self.query_one("#settings-url-input", Input).value.strip()
        if not url:
            self.app.notify("Enter a URL", severity="warning")
            return
        self._apply_url(url)

    @on(Input.Submitted, "#settings-url-input")
    def on_url_enter(self) -> None:
        self.on_apply()

    @work
    async def _apply_url(self, url: str) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        status = self.query_one("#settings-conn-status", Static)
        status.update("[dim]Testing…[/dim]")

        await client._http.aclose()
        client._http = httpx.AsyncClient(base_url=url, timeout=60.0)
        client.base_url = url

        connected = await client.health_check()
        if connected:
            self.query_one("#settings-current-url", Static).update(
                f"Current: [bold]{url}[/bold]"
            )
            status.update("[green]● Connected[/green]")
            self.app.notify(f"Connected to {url}")
        else:
            status.update(f"[red]● Cannot connect to {url}[/red]")
            self.app.notify(f"Cannot connect to {url}", severity="error")
