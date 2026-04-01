"""Chat bubble widget — renders user / assistant / system messages."""
from __future__ import annotations

from textual.widgets import Static


class ChatMessage(Static):
    def __init__(
        self,
        role: str,
        content: str,
        model: str = "",
        usage: dict | None = None,
    ) -> None:
        self.role = role
        self.msg_content = content
        self.model = model
        self.usage = usage
        super().__init__(self._markup(), classes=f"chat-message {role}")

    def _markup(self) -> str:
        if self.role == "user":
            return f"[bold blue]You >[/bold blue] {self.msg_content}"

        if self.role == "assistant":
            meta = f" [dim]via {self.model}[/dim]" if self.model else ""
            tokens = ""
            if self.usage:
                total = self.usage.get("total_tokens", 0)
                if total:
                    tokens = f" [dim]({total} tokens)[/dim]"
            return (
                f"[bold green]Assistant{meta}{tokens}[/bold green]\n"
                f"{self.msg_content}"
            )

        # system / error
        return f"[bold yellow]System:[/bold yellow] {self.msg_content}"
