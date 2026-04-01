"""ResultTable — thin DataTable wrapper used by the Results screen."""
from __future__ import annotations

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import DataTable, Label


class ResultTable(Widget):
    """DataTable with a title label and helpers for loading benchmark result rows."""

    def __init__(self, title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title

    def compose(self) -> ComposeResult:
        if self._title:
            yield Label(self._title, classes="section-header")
        yield DataTable(id="dt", show_cursor=True)

    def load(self, columns: list[str], rows: list[list]) -> None:
        """Replace content with new columns + rows."""
        dt = self.query_one("#dt", DataTable)
        dt.clear(columns=True)
        dt.add_columns(*columns)
        for row in rows:
            dt.add_row(*[str(v) for v in row])
