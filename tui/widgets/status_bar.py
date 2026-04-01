"""Bottom status bar — shows current user and API connection state."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    def compose(self) -> ComposeResult:
        yield Label("[dim]Not logged in[/dim]", id="status-user")
        yield Label("[red]● Disconnected[/red]", id="status-conn")

    def update_user(self, user: dict | None) -> None:
        lbl = self.query_one("#status-user", Label)
        if user:
            lbl.update(f"[bold]{user['username']}[/bold] [{user['user_type']}]")
        else:
            lbl.update("[dim]Not logged in[/dim]")

    def update_connection(self, connected: bool) -> None:
        lbl = self.query_one("#status-conn", Label)
        if connected:
            lbl.update("[green]● Connected[/green]")
        else:
            lbl.update("[red]● Disconnected[/red]")
