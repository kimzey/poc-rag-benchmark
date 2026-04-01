"""Chunk viewer widget — shows retrieved chunks with scores and access levels."""
from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import Label, Static

from tui.client import RetrievedChunk

_LEVEL_COLOR = {
    "customer_kb": "green",
    "internal_kb": "yellow",
    "confidential_kb": "red",
}


class ChunkItem(Static):
    def __init__(self, num: int, chunk: RetrievedChunk) -> None:
        color = _LEVEL_COLOR.get(chunk.access_level, "white")
        filled = int(chunk.score * 10)
        bar = "█" * filled + "░" * (10 - filled)
        preview = escape(chunk.content[:120].replace("\n", " "))
        title = escape(chunk.title)
        markup = (
            f"[bold]{num}. {title}[/bold]\n"
            f"[{color}]{bar}[/{color}] {chunk.score:.2f} "
            f"[{color}][[{chunk.access_level}]][/{color}]\n"
            f"[dim]{preview}…[/dim]"
        )
        super().__init__(markup, classes="chunk-item")


class ChunkViewer(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Retrieved Chunks", id="chunk-header")
        yield ScrollableContainer(id="chunks-list")

    def update_chunks(self, chunks: list[RetrievedChunk]) -> None:
        container = self.query_one("#chunks-list", ScrollableContainer)
        container.remove_children()
        if not chunks:
            container.mount(Static("[dim]No chunks retrieved[/dim]", classes="chunk-empty"))
            return
        for i, chunk in enumerate(chunks, 1):
            container.mount(ChunkItem(i, chunk))
