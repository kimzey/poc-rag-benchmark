<!-- Generated: 2026-04-01 | Files scanned: 13 | Token estimate: ~700 -->

# TUI (Terminal User Interface) Codemap

**Last Updated:** 2026-04-01  
**Phase:** 6 (Textual TUI application)  
**Entry Points:** `tui/app.py` (RAGTuiApp), `python -m tui` or `make tui`

## Application Architecture

```
tui/app.py (RAGTuiApp — Textual App)
├─ compose() → Layout
│  ├─ Header()                          [top bar]
│  ├─ Horizontal(id="main-layout")      [sidebar + content switcher]
│  │  ├─ NavigationSidebar(id="sidebar") [F1-F7 navigation + Login]
│  │  └─ ContentSwitcher(id="content")   [Panel switcher]
│  │     ├─ DashboardPanel (id="dashboard")      [Phase 1, implemented]
│  │     ├─ ChatPanel (id="chat")                [Phase 1, implemented]
│  │     ├─ PlaceholderPanel ("Benchmarks")      [Phase 2, stub]
│  │     ├─ PlaceholderPanel ("Results")        [Phase 2, stub]
│  │     ├─ PlaceholderPanel ("Documents")      [Phase 3, stub]
│  │     ├─ PlaceholderPanel ("Tests")          [Phase 3, stub]
│  │     └─ PlaceholderPanel ("Settings")       [Phase 4, stub]
│  │
│  ├─ StatusBar(id="status-bar")        [bottom: connection status, user info]
│  └─ Footer()                          [keybindings legend]
│
├─ BINDINGS (keybindings)
│  ├─ q:      quit
│  ├─ f1-f7:  switch screens
│  ├─ l:      show login dialog
│  └─ ctrl+l: clear chat history
│
├─ client: RAGClient (HTTP async client)
│  ├─ base_url: str  (default: http://localhost:8000)
│  ├─ token: str | None
│  └─ current_user: dict | None
│
└─ action_* methods (handlers for keybindings)
   ├─ action_show_dashboard()
   ├─ action_show_chat()
   ├─ action_login()
   └─ ... (one per binding)
```

## Screens (Implemented)

### DashboardPanel (`tui/screens/dashboard.py`)

```
Dashboard
├─ Title: "Dashboard"
├─ Status box: API connection status + logged-in user info
├─ Model info box: LLM provider, embedding model, vector DB
├─ Quick stats: document count, indexed chunks, etc.
└─ Instructions: "Use F1-F7 to navigate"
```

### ChatPanel (`tui/screens/chat.py`)

```
Chat
├─ Message history (scrollable)
│  ├─ ChatMessage (role="assistant", content="...", timestamp)
│  ├─ ChatMessage (role="user", content="...", timestamp)
│  └─ ... (history)
│
├─ Input box (bottom)
│  └─ Text input for user query
│
├─ Retrieved chunks panel (right side, collapsible)
│  └─ ChunkViewer (scrollable list of RetrievedChunk objects)
│     ├─ [doc_id] title (access_level) — score: 0.95
│     ├─ content preview...
│     └─ [expand to see full content]
│
└─ Send button (or Enter key)
```

## Widgets

### ChatMessage (`tui/widgets/chat_message.py`)

```python
class ChatMessage(Static):
    def __init__(self, role: str, content: str, timestamp: str | None = None):
        # Render with role-specific styling (bold for assistant, normal for user)
        # Include optional timestamp
        # Handle long content with word wrap
```

### ChunkViewer (`tui/widgets/chunk_viewer.py`)

```python
class ChunkViewer(Static):
    """Display list of RetrievedChunk objects with expandable previews."""
    def __init__(self, chunks: list[RetrievedChunk]):
        # Render each chunk:
        # [doc_id] title (access_level) — score: 0.95
        # Content preview (first 100 chars)
        # Expand button
```

### LoginModal (`tui/widgets/login_dialog.py`)

```python
class LoginModal(ModalScreen):
    """Modal dialog for login."""
    BINDINGS = [
        ("escape", "cancel_login", "Cancel"),
        ("enter", "submit_login", "Login"),
    ]

    def compose(self) -> ComposeResult:
        yield Input(id="username", placeholder="Username")
        yield Input(id="password", placeholder="Password")
        yield Button("Login", variant="primary")
        yield Button("Cancel")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "login-btn":
            username = self.query_one("#username", Input).value
            password = self.query_one("#password", Input).value
            # Call client.login(username, password)
            # Update status bar + dismiss modal
```

### StatusBar (`tui/widgets/status_bar.py`)

```python
class StatusBar(Static):
    """Bottom status bar showing connection + user state."""
    def render(self) -> str:
        if client.is_logged_in:
            user = client.current_user["username"]
            return f"[bold green]✓[/bold green] Connected — {user}"
        else:
            return "[dim]Not logged in — Press L to login[/dim]"
```

## HTTP Client (`tui/client.py`)

```python
class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: str | None = None
        self.current_user: dict | None = None
        self._http = httpx.AsyncClient(...)

    # Auth
    async def login(username: str, password: str) → dict
    async def me() → dict
    def logout() → None

    # Chat & Retrieval
    async def chat(
        messages: list[dict],
        top_k: int = 3,
        collection: str | None = None,
    ) → ChatResult:
        # POST /api/v1/chat/completions
        # Returns ChatResult(answer, retrieved_chunks, model, usage)

    async def search(query: str, top_k: int = 5) → dict
        # GET /api/v1/documents/search?q=...&top_k=...

    async def submit_feedback(
        query_id: str,
        rating: int,
        comment: str = ""
    ) → dict:
        # POST /api/v1/feedback

    # Lifecycle
    async def health_check() → bool
    async def close() → None
    is_logged_in: bool (property)
```

## Data Models (`tui/client.py`)

```python
@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    content: str
    access_level: str
    score: float

@dataclass
class ChatResult:
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    model: str
    usage: dict | None = None

class AuthError(Exception): ...
class ServerConnectionError(Exception): ...
```

## Navigation Flow

```
Start
  ↓
[Login Dialog] ← Press L, Escape to cancel
  ↓
[Dashboard] (F1) ← Default screen
  ↓ F2
[Chat] ← Send query
  ↓ (see retrieved chunks in right pane)
[Results] (F4) ← View all retrieved chunks
  ↓ F3-F7
[Benchmarks / Documents / Tests / Settings] (Phase 2-4, stubs)
  ↓ Q
[Quit]
```

## CSS (`tui/styles/app.tcss`)

- `#sidebar`: Width 20 columns, vertical scrolling
- `#content`: Main panel, horizontal scrolling
- `.nav-btn`: Navigation button styling (focus color change)
- `#status-bar`: Dark background, small font
- `.placeholder-panel`: Centered text, dim color
- `.chat-message-user`: Light background
- `.chat-message-assistant`: Highlight background
- `.chunk-viewer`: Scrollable list, borders

## Configuration (`tui/config.py`)

```python
class Settings(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    # (load from .env, default to localhost)
```

## Entry Point (`tui/__main__.py`)

```python
if __name__ == "__main__":
    app = RAGTuiApp()
    app.run()
```

## Launch Commands

```bash
python -m tui              # Run TUI
make tui                   # Convenience wrapper (uv run python -m tui)
```

## Related Codemaps

- **[backend.md](backend.md)** — API server this TUI calls
- **[architecture.md](architecture.md)** — Overall system structure
- **[dependencies.md](dependencies.md)** — External dependencies (textual, httpx)
