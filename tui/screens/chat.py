"""Chat screen — interactive RAG query with retrieved chunk viewer."""
from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from tui.widgets.chat_message import ChatMessage
from tui.widgets.chunk_viewer import ChunkViewer


class ChatPanel(Widget):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history: list[dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="chat-layout"):
            with Vertical(id="chat-main"):
                yield Label("RAG Chat", id="chat-title")
                yield ScrollableContainer(id="messages")
                with Horizontal(id="chat-input-area"):
                    yield Input(
                        placeholder="Type a message… (Enter to send)",
                        id="chat-input",
                    )
                    yield Button("Send", id="btn-send", variant="primary")
                yield Label("", id="chat-status")
            yield ChunkViewer()

    def on_show(self) -> None:
        self.query_one("#chat-input", Input).focus()

    # ── send ──────────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-send")
    def on_send_btn(self) -> None:
        self._send()

    @on(Input.Submitted, "#chat-input")
    def on_input_enter(self) -> None:
        self._send()

    def _send(self) -> None:
        inp = self.query_one("#chat-input", Input)
        content = inp.value.strip()
        if not content:
            return
        if not self.app.client.is_logged_in:  # type: ignore[attr-defined]
            self.app.notify("Please login first — press L", severity="warning")
            return
        inp.value = ""
        inp.focus()

        self._history.append({"role": "user", "content": content})
        box = self.query_one("#messages", ScrollableContainer)
        box.mount(ChatMessage("user", content))
        box.scroll_end(animate=False)

        self._do_chat()

    @work(exclusive=True)
    async def _do_chat(self) -> None:
        client = self.app.client  # type: ignore[attr-defined]
        box = self.query_one("#messages", ScrollableContainer)
        status = self.query_one("#chat-status", Label)

        status.update("[dim]Retrieving…[/dim]")
        loading = Static("● ● ●", classes="chat-message loading")
        box.mount(loading)
        box.scroll_end(animate=False)

        try:
            result = await client.chat(self._history)
        except Exception as exc:
            loading.remove()
            box.mount(ChatMessage("system", f"Error: {exc}"))
            box.scroll_end(animate=False)
            status.update(f"[red]{exc}[/red]")
            return

        loading.remove()
        self._history.append({"role": "assistant", "content": result.answer})
        box.mount(ChatMessage("assistant", result.answer, model=result.model, usage=result.usage))
        box.scroll_end(animate=False)

        self.query_one(ChunkViewer).update_chunks(result.retrieved_chunks)
        n = len(result.retrieved_chunks)
        status.update(f"[dim]Model: {result.model} | {n} chunk{'s' if n != 1 else ''} retrieved[/dim]")

    # ── clear ─────────────────────────────────────────────────────────────────

    def action_clear_chat(self) -> None:
        self.query_one("#messages", ScrollableContainer).remove_children()
        self._history.clear()
        self.query_one(ChunkViewer).update_chunks([])
        self.query_one("#chat-status", Label).update("")
        self.app.notify("Chat cleared")
