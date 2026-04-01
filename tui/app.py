"""
RAG Spike TUI — main application.

Run:  python -m tui   or   make tui
"""
from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
    Label,
    Rule,
    Static,
)

from tui.client import RAGClient
from tui.config import settings
from tui.screens.benchmarks import BenchmarksPanel
from tui.screens.chat import ChatPanel
from tui.screens.dashboard import DashboardPanel
from tui.screens.results import ResultsPanel
from tui.widgets.login_dialog import LoginModal
from tui.widgets.status_bar import StatusBar

# Panels not yet implemented — show placeholder
_PLACEHOLDER_PANELS = [
    ("documents", "Documents", "Phase 3"),
    ("tests", "Tests", "Phase 3"),
    ("settings", "Settings", "Phase 4"),
]


class PlaceholderPanel(Static):
    """Stub for panels coming in later phases."""

    def __init__(self, title: str, phase: str, **kwargs) -> None:
        super().__init__(
            f"[bold]{title}[/bold]\n\n"
            f"[dim]Coming in {phase}[/dim]\n\n"
            "See [italic]plan.md[/italic] for implementation details.",
            classes="placeholder-panel",
            **kwargs,
        )


class NavigationSidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("RAG Spike TUI", id="sidebar-brand")
        yield Rule()
        yield Button("[F1] Dashboard", id="nav-dashboard", classes="nav-btn")
        yield Button("[F2] Chat",      id="nav-chat",      classes="nav-btn")
        yield Button("[F3] Benchmarks",id="nav-benchmarks",classes="nav-btn")
        yield Button("[F4] Results",   id="nav-results",   classes="nav-btn")
        yield Button("[F5] Documents", id="nav-documents", classes="nav-btn")
        yield Button("[F6] Tests",     id="nav-tests",     classes="nav-btn")
        yield Button("[F7] Settings",  id="nav-settings",  classes="nav-btn")
        yield Rule()
        yield Button("[L] Login",  id="nav-login",  variant="primary", classes="nav-btn")
        yield Button("Logout",     id="nav-logout",                    classes="nav-btn")


class RAGTuiApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "RAG Spike TUI"

    BINDINGS = [
        Binding("q",      "quit",            "Quit"),
        Binding("f1",     "show_dashboard",  "Dashboard"),
        Binding("f2",     "show_chat",       "Chat"),
        Binding("f3",     "show_benchmarks", "Benchmarks"),
        Binding("f4",     "show_results",    "Results"),
        Binding("f5",     "show_documents",  "Documents"),
        Binding("f6",     "show_tests",      "Tests"),
        Binding("f7",     "show_settings",   "Settings"),
        Binding("l",      "login",           "Login"),
        Binding("ctrl+l", "clear_chat",      "Clear Chat", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.client = RAGClient(settings.api_base_url)

    # ── layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-layout"):
            yield NavigationSidebar(id="sidebar")
            with ContentSwitcher(id="content", initial="dashboard"):
                yield DashboardPanel(id="dashboard")
                yield ChatPanel(id="chat")
                yield BenchmarksPanel(id="benchmarks")
                yield ResultsPanel(id="results")
                for panel_id, title, phase in _PLACEHOLDER_PANELS:
                    yield PlaceholderPanel(title, phase, id=panel_id)
        yield StatusBar(id="status-bar")
        yield Footer()

    # ── startup ───────────────────────────────────────────────────────────────

    async def on_mount(self) -> None:
        connected = await self.client.health_check()
        self.query_one(StatusBar).update_connection(connected)
        self._set_active("dashboard")

    # ── navigation ────────────────────────────────────────────────────────────

    def action_nav(self, panel_id: str) -> None:
        self.query_one(ContentSwitcher).current = panel_id
        self._set_active(panel_id)

    def _set_active(self, panel_id: str) -> None:
        for btn in self.query(".nav-btn"):
            btn.remove_class("active")
        try:
            self.query_one(f"#nav-{panel_id}", Button).add_class("active")
        except Exception:
            pass

    def action_show_dashboard(self)  -> None: self.action_nav("dashboard")
    def action_show_chat(self)       -> None: self.action_nav("chat")
    def action_show_benchmarks(self) -> None: self.action_nav("benchmarks")
    def action_show_results(self)    -> None: self.action_nav("results")
    def action_show_documents(self)  -> None: self.action_nav("documents")
    def action_show_tests(self)      -> None: self.action_nav("tests")
    def action_show_settings(self)   -> None: self.action_nav("settings")

    # ── sidebar buttons ───────────────────────────────────────────────────────

    @on(Button.Pressed, "#nav-dashboard")
    def _nb_dashboard(self)  -> None: self.action_nav("dashboard")
    @on(Button.Pressed, "#nav-chat")
    def _nb_chat(self)       -> None: self.action_nav("chat")
    @on(Button.Pressed, "#nav-benchmarks")
    def _nb_benchmarks(self) -> None: self.action_nav("benchmarks")
    @on(Button.Pressed, "#nav-results")
    def _nb_results(self)    -> None: self.action_nav("results")
    @on(Button.Pressed, "#nav-documents")
    def _nb_documents(self)  -> None: self.action_nav("documents")
    @on(Button.Pressed, "#nav-tests")
    def _nb_tests(self)      -> None: self.action_nav("tests")
    @on(Button.Pressed, "#nav-settings")
    def _nb_settings(self)   -> None: self.action_nav("settings")

    # ── auth ──────────────────────────────────────────────────────────────────

    def action_login(self) -> None:
        self.push_screen(LoginModal(self.client), self._on_login_result)

    def _on_login_result(self, user: dict | None) -> None:
        if user:
            self.query_one(StatusBar).update_user(user)
            self.notify(f"Logged in as {user['username']} ({user['user_type']})")

    @on(Button.Pressed, "#nav-login")
    def _nb_login(self) -> None:
        self.action_login()

    @on(Button.Pressed, "#nav-logout")
    def _nb_logout(self) -> None:
        if self.client.is_logged_in:
            self.client.logout()
            self.query_one(StatusBar).update_user(None)
            self.notify("Logged out")
        else:
            self.notify("Not logged in", severity="warning")

    # ── chat helpers ──────────────────────────────────────────────────────────

    def action_clear_chat(self) -> None:
        self.query_one(ChatPanel).action_clear_chat()

    # ── cleanup ───────────────────────────────────────────────────────────────

    async def on_unmount(self) -> None:
        await self.client.close()
