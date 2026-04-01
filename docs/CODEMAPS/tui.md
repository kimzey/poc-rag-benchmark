<!-- Generated: 2026-04-01 | Files scanned: 17 | Token estimate: ~900 -->

# TUI (Terminal User Interface) Codemap

**Last Updated:** 2026-04-01 (Updated for Phase 3: Embedding Model Scorecard)  
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
│  │     ├─ BenchmarksPanel (id="benchmarks")    [Phase 2, implemented ✓]
│  │     ├─ ResultsPanel (id="results")          [Phase 2, implemented ✓]
│  │     ├─ PlaceholderPanel ("Documents")       [Phase 3, stub]
│  │     ├─ PlaceholderPanel ("Tests")           [Phase 3, stub]
│  │     └─ PlaceholderPanel ("Settings")        [Phase 4, stub]
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

## Screens (Implemented & Phase 2 Complete)

### Phase 1: Dashboard & Chat (Implemented)

**DashboardPanel** (`tui/screens/dashboard.py`)
```
├─ Title: "Dashboard"
├─ Status box: API connection + user info
├─ Model info: LLM provider, embedding, vector DB
├─ Stats: document count, chunks, index status
└─ Instructions: keybinding reference
```

**ChatPanel** (`tui/screens/chat.py`)
```
├─ Message history (scrollable, per-session)
├─ Input box: user query text field
├─ Retrieved chunks pane (right side)
│  └─ ChunkViewer: list with doc_id, score, preview
└─ Send button (or Enter)
```

### Phase 2: Benchmark & Results (Implemented ✓)

**BenchmarksPanel** (`tui/screens/benchmarks.py`)
```
BenchmarksPanel
├─ TabbedContent(id="bench-tabs")
│  ├─ _VectorDBTab
│  │  ├─ Checkboxes: Qdrant, pgvector, Milvus, OpenSearch
│  │  ├─ Input: N vectors (default 10000)
│  │  ├─ Note: "Requires Docker: make up-db"
│  │  ├─ Button: "Run Vector DB Benchmark"
│  │  └─ BenchmarkProgress widget (RichLog + cancel)
│  │
│  ├─ _RAGFrameworkTab
│  │  ├─ Checkboxes: bare_metal, LlamaIndex, LangChain, Haystack
│  │  ├─ Checkbox: --no-llm (retrieval only)
│  │  ├─ Note: "OPENROUTER_API_KEY required"
│  │  ├─ Button: "Run RAG Framework Benchmark"
│  │  └─ BenchmarkProgress widget
│  │
│  ├─ _EmbeddingModelTab
│  │  ├─ Checkboxes: multilingual_e5, bge_m3, mxbai, wangchanberta, openai_large, openai_small, cohere_v3
│  │  ├─ Input: top_k (default 3)
│  │  ├─ Note: "OPENAI_API_KEY / COHERE_API_KEY required for api models"
│  │  ├─ Button: "Run Embedding Benchmark"
│  │  └─ BenchmarkProgress widget
│  │
│  └─ _LLMProviderTab
│     ├─ API key status display (live check: OPENROUTER, OPENAI, ANTHROPIC, COHERE)
│     ├─ Input: top_k (default 3)
│     ├─ Button: "Run LLM Provider Benchmark"
│     └─ BenchmarkProgress widget
```

**ResultsPanel** (`tui/screens/results.py`)
```
ResultsPanel
├─ TabbedContent(id="results-tabs")
│  ├─ _VectorDBResult (reads latest JSON from benchmarks/vector-db/results/)
│  │  └─ ResultTable: Cols=[DB, Vectors, Idx(s), Throughput, p50(ms), p95(ms), p99(ms), QPS, Filter p95, Recall@10]
│  │
│  ├─ _RAGFrameworkResult (reads from benchmarks/rag-framework/results/)
│  │  ├─ ResultTable: Indexing metrics [Framework, Chunks, Idx(ms), LOC]
│  │  └─ ResultTable: Query latency [Framework, Min(ms), Avg(ms), Max(ms), p95(ms)]
│  │
│  ├─ _EmbeddingModelResult (reads from benchmarks/embedding-model/results/)
│  │  ├─ ResultTable: Quality [Model, Thai Recall, Eng Recall, Overall, MRR]
│  │  ├─ ResultTable: Latency & Cost [Model, Idx(ms), Avg Query(ms), Cost/1M, Self-host]
│  │  └─ ResultTable: Weighted Scorecard [Rank, Model, Weighted Score, Dims, Max Tokens, Lock-in]
│  │
│  └─ _LLMProviderResult (reads from benchmarks/llm-provider/results/)
│     ├─ ResultTable: Quality [Provider, Overall F1, Thai F1, Questions]
│     └─ ResultTable: Cost [Provider, Avg Lat(ms), Total Cost($), $/1M in, $/1M out]
```

## Widgets

### Phase 1 Widgets

**ChatMessage** (`tui/widgets/chat_message.py`)
- Renders individual messages with role-specific styling
- Timestamp display, word wrapping for long content

**ChunkViewer** (`tui/widgets/chunk_viewer.py`)
- Display list of RetrievedChunk objects
- Shows: [doc_id] title (access_level) — score: 0.95
- Expandable previews

**LoginModal** (`tui/widgets/login_dialog.py`)
- Modal dialog for JWT authentication
- Username + Password inputs
- Escape to cancel, Enter to submit

**StatusBar** (`tui/widgets/status_bar.py`)
- Bottom status bar showing connection + user state
- Live updates: "✓ Connected — alice_admin" or "Not logged in — Press L"

### Phase 2 Widgets (New)

**BenchmarkProgress** (`tui/widgets/benchmark_progress.py`)
```python
class BenchmarkProgress(Widget):
    """Real-time subprocess output widget for benchmarks."""
    
    state: BenchmarkState  # IDLE, RUNNING, DONE, ERROR, CANCELLED
    
    compose() → ComposeResult:
        └─ Horizontal (header)
            ├─ Label: state indicator (Idle / ● Running… / ✓ Done / ✗ Error / ⊘ Cancelled)
            └─ Button: Cancel (disabled when IDLE)
        └─ RichLog: real-time output stream (highlight=True)
    
    run_command(cmd: list[str], cwd: str) → None
        • Starts async subprocess
        • Streams stdout line-by-line into RichLog
        • Updates state label in real-time
        • Exit code check: 0=Done, non-zero=Error
    
    _stream_subprocess() → @work(thread=True)
        • Uses subprocess.Popen with start_new_session=True
        • Kills process group on cancel() via SIGTERM
        • Thread-safe updates via call_from_thread()
    
    Key: Benchmarks can run 5-30 min, widget shows live progress
```

**ResultTable** (`tui/widgets/result_table.py`)
```python
class ResultTable(Widget):
    """Thin DataTable wrapper for benchmark results."""
    
    compose() → ComposeResult:
        ├─ Label: title (optional, e.g., "Indexing", "Query Latency")
        └─ DataTable: columns + rows
    
    load(columns: list[str], rows: list[list]) → None
        • Clear existing data
        • Add column headers
        • Add rows (auto-stringify)
        
    Usage: Each ResultsPanel tab uses 1-2 ResultTable widgets
    Data source: Latest JSON in benchmarks/*/results/ directory
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
[Dashboard] (F1) ← Default screen, system status
  ↓ F2
[Chat] (F2) ← RAG query + retrieved chunks
  ↓
[Benchmarks] (F3) ← Phase 2: Run or monitor benchmarks (4 tabs)
  │  └─ Select vector DBs / frameworks / models / providers → click Run
  │     └─ BenchmarkProgress widget streams live output
  │        └─ Live result JSON written to benchmarks/*/results/
  ↓
[Results] (F4) ← Phase 2: View latest benchmark JSON results (4 tabs)
  │  └─ Auto-loads latest JSON from benchmarks/*/results/ directories
  │     └─ ResultTable widgets display metrics tables
  ↓
[Documents] (F5) ← Phase 3, stub
  ↓
[Tests] (F6) ← Phase 3, stub
  ↓
[Settings] (F7) ← Phase 4, stub
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
