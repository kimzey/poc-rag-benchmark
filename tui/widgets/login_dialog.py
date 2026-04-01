"""Login modal dialog — pops up over the main screen."""
from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from tui.client import AuthError, RAGClient, ServerConnectionError

# Test-user credentials for PoC quick-login
_QUICK_USERS = [
    ("admin", "alice_admin", "admin123"),
    ("employee", "bob_employee", "emp123"),
    ("customer", "carol_customer", "cust123"),
    ("service", "svc_line_bot", "svc123"),
]


class LoginModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, client: RAGClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        with Vertical(id="login-dialog"):
            yield Label("Login to RAG Spike", id="login-title")
            yield Label("", id="login-error")
            yield Label("Username")
            yield Input(placeholder="alice_admin", id="login-username")
            yield Label("Password")
            yield Input(placeholder="password", password=True, id="login-password")
            yield Label("Quick login:")
            with Horizontal(id="quick-logins"):
                for role, _user, _pw in _QUICK_USERS:
                    yield Button(role, id=f"quick-{role}")
            with Horizontal(id="login-buttons"):
                yield Button("Login", id="btn-login-submit", variant="primary")
                yield Button("Cancel", id="btn-login-cancel")

    # ── quick-fill handlers ───────────────────────────────────────────────────

    @on(Button.Pressed, "#quick-admin")
    def fill_admin(self) -> None:
        self._fill("alice_admin", "admin123")

    @on(Button.Pressed, "#quick-employee")
    def fill_employee(self) -> None:
        self._fill("bob_employee", "emp123")

    @on(Button.Pressed, "#quick-customer")
    def fill_customer(self) -> None:
        self._fill("carol_customer", "cust123")

    @on(Button.Pressed, "#quick-service")
    def fill_service(self) -> None:
        self._fill("svc_line_bot", "svc123")

    def _fill(self, username: str, password: str) -> None:
        self.query_one("#login-username", Input).value = username
        self.query_one("#login-password", Input).value = password

    # ── submit ────────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-login-submit")
    def on_submit_btn(self) -> None:
        self._submit()

    @on(Input.Submitted)
    def on_input_enter(self) -> None:
        self._submit()

    def _submit(self) -> None:
        username = self.query_one("#login-username", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        self._do_login(username, password)

    @work(exclusive=True)
    async def _do_login(self, username: str, password: str) -> None:
        error = self.query_one("#login-error", Label)
        error.update("")
        if not username or not password:
            error.update("[red]Username and password required[/red]")
            return
        try:
            user = await self.client.login(username, password)
            self.dismiss(user)
        except AuthError as exc:
            error.update(f"[red]{exc}[/red]")
        except ServerConnectionError as exc:
            error.update(f"[red]{exc}[/red]")
        except Exception as exc:
            error.update(f"[red]Error: {exc}[/red]")

    # ── cancel ────────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-login-cancel")
    def on_cancel_btn(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
