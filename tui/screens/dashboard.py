"""Dashboard screen — system status overview and quick actions."""
from __future__ import annotations

import os

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, Rule, Static


class DashboardPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Dashboard", id="dashboard-title")
        with Horizontal(id="dashboard-body"):
            with Vertical(id="dash-status"):
                yield Label("System Status", classes="section-header")
                yield Static("Checking connection…", id="dash-conn")
                yield Static("", id="dash-user")
                yield Rule()
                yield Label("API Keys", classes="section-header")
                yield Static("", id="dash-keys")
            with Vertical(id="dash-actions"):
                yield Label("Quick Actions", classes="section-header")
                yield Button("Chat [F2]", id="dash-btn-chat", variant="primary")
                yield Button("Benchmarks [F3]", id="dash-btn-bench")
                yield Button("Results [F4]", id="dash-btn-results")
                yield Button("Tests [F6]", id="dash-btn-tests")
                yield Rule()
                yield Button("Login [L]", id="dash-btn-login", variant="success")

    def on_mount(self) -> None:
        self._refresh()

    def on_show(self) -> None:
        self._refresh()

    @work
    async def _refresh(self) -> None:
        client = self.app.client  # type: ignore[attr-defined]

        # Connection
        connected = await client.health_check()
        self.query_one("#dash-conn", Static).update(
            "[green]● API Connected[/green]" if connected
            else "[red]● API Disconnected[/red] — run: make api-run"
        )

        # User
        if client.current_user:
            u = client.current_user
            perms = ", ".join(u.get("permissions", [])[:4])
            self.query_one("#dash-user", Static).update(
                f"[bold]{u['username']}[/bold] ({u['user_type']})\n"
                f"[dim]{perms}[/dim]"
            )
        else:
            self.query_one("#dash-user", Static).update("[dim]Not logged in — press L[/dim]")

        # API keys
        keys = [
            ("OPENROUTER", "OPENROUTER_API_KEY"),
            ("OPENAI", "OPENAI_API_KEY"),
            ("ANTHROPIC", "ANTHROPIC_API_KEY"),
            ("COHERE", "COHERE_API_KEY"),
        ]
        lines = [
            f"{'[green]✓[/green]' if os.getenv(k) else '[red]✗[/red]'} {name}"
            for name, k in keys
        ]
        self.query_one("#dash-keys", Static).update("\n".join(lines))

    # ── quick actions ─────────────────────────────────────────────────────────

    @on(Button.Pressed, "#dash-btn-chat")
    def go_chat(self) -> None:
        self.app.action_nav("chat")  # type: ignore[attr-defined]

    @on(Button.Pressed, "#dash-btn-bench")
    def go_bench(self) -> None:
        self.app.action_nav("benchmarks")  # type: ignore[attr-defined]

    @on(Button.Pressed, "#dash-btn-results")
    def go_results(self) -> None:
        self.app.action_nav("results")  # type: ignore[attr-defined]

    @on(Button.Pressed, "#dash-btn-tests")
    def go_tests(self) -> None:
        self.app.action_nav("tests")  # type: ignore[attr-defined]

    @on(Button.Pressed, "#dash-btn-login")
    def do_login(self) -> None:
        self.app.action_login()  # type: ignore[attr-defined]
