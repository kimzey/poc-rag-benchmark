"""Documents screen — search and upload documents via the RAG API."""
from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, Rule, Select, Static


_ACCESS_LEVELS: list[tuple[str, str]] = [
    ("Internal KB (employee+)", "internal_kb"),
    ("Customer KB (public)", "customer_kb"),
    ("Confidential (admin only)", "confidential_kb"),
]


class DocumentsPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Documents", id="docs-title")
        with Vertical(id="docs-body"):
            yield Label("Search Documents", classes="section-header")
            with Horizontal(id="docs-search-row"):
                yield Input(placeholder="Search query…", id="docs-search-input")
                yield Button("Search", id="docs-btn-search", variant="primary")
            yield DataTable(id="docs-table", show_cursor=True)
            yield Rule()
            yield Label("Upload Document  [dim](employee+ only)[/dim]", classes="section-header")
            with Horizontal(id="docs-upload-row"):
                yield Input(placeholder="File path e.g. datasets/hr_policy_th.md", id="docs-file-path")
                yield Select(
                    _ACCESS_LEVELS,
                    value="internal_kb",
                    id="docs-access-level",
                )
                yield Button("Upload", id="docs-btn-upload", variant="success")
            yield Static("", id="docs-status")
            yield Static("", id="docs-collections-info")

    def on_mount(self) -> None:
        dt = self.query_one("#docs-table", DataTable)
        dt.add_columns("Doc ID", "Title", "Score", "Access Level", "Snippet")
        self._refresh_collections()

    def on_show(self) -> None:
        self._refresh_collections()

    @work
    async def _refresh_collections(self) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        info_lbl = self.query_one("#docs-collections-info", Static)
        if not client.is_logged_in:
            info_lbl.update("[dim]Login to see collection info — press L[/dim]")
            return
        try:
            info = await client.list_collections()
            levels = ", ".join(info.get("visible_access_levels", []))
            total = info.get("total_visible_docs", 0)
            info_lbl.update(f"[dim]Visible levels: {levels} | Total docs: {total}[/dim]")
        except Exception as exc:
            info_lbl.update(f"[red]{exc}[/red]")

    # ── search ────────────────────────────────────────────────────────────────

    @on(Input.Submitted, "#docs-search-input")
    def on_search_enter(self) -> None:
        self._do_search_if_ready()

    @on(Button.Pressed, "#docs-btn-search")
    def on_search_btn(self) -> None:
        self._do_search_if_ready()

    def _do_search_if_ready(self) -> None:
        q = self.query_one("#docs-search-input", Input).value.strip()
        if not q:
            return
        if not self.app.client.is_logged_in:  # type: ignore[attr-defined]
            self.app.notify("Please login first — press L", severity="warning")
            return
        self._do_search(q)

    @work
    async def _do_search(self, q: str) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        status = self.query_one("#docs-status", Static)
        status.update("[dim]Searching…[/dim]")
        dt = self.query_one("#docs-table", DataTable)
        dt.clear()
        try:
            data = await client.search(q, top_k=10)
            results = data.get("results", [])
            for r in results:
                snippet = r.get("content", "")
                if len(snippet) > 60:
                    snippet = snippet[:60] + "…"
                dt.add_row(
                    r.get("doc_id", ""),
                    r.get("title", ""),
                    f"{r.get('score', 0):.3f}",
                    r.get("access_level", ""),
                    snippet,
                )
            status.update(f"[dim]{len(results)} result(s) for '{q}'[/dim]")
        except Exception as exc:
            status.update(f"[red]Search error: {exc}[/red]")

    # ── upload ────────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#docs-btn-upload")
    def on_upload_btn(self) -> None:
        path = self.query_one("#docs-file-path", Input).value.strip()
        if not path:
            self.app.notify("Enter a file path", severity="warning")
            return
        if not self.app.client.is_logged_in:  # type: ignore[attr-defined]
            self.app.notify("Please login first — press L", severity="warning")
            return
        access = self.query_one("#docs-access-level", Select).value
        self._do_upload(path, str(access))

    @work
    async def _do_upload(self, path: str, access_level: str) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        status = self.query_one("#docs-status", Static)
        status.update("[dim]Uploading…[/dim]")
        try:
            result = await client.upload_document(path, access_level)
            status.update(
                f"[green]✓ Uploaded: {result['doc_id']} — {result['message']}[/green]"
            )
            self.query_one("#docs-file-path", Input).value = ""
            self._refresh_collections()
        except FileNotFoundError:
            status.update(f"[red]File not found: {path}[/red]")
        except Exception as exc:
            status.update(f"[red]Upload error: {exc}[/red]")
