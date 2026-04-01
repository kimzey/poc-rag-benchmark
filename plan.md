# Implementation Plan: GUI Terminal (TUI) for RAG Spike

## Overview

สร้าง Terminal User Interface (TUI) ด้วย **Textual** framework เพื่อให้ผู้ใช้สามารถ interact กับ RAG API, รัน benchmarks ทุก phase, ดู results/reports, และทำ interactive RAG queries ผ่าน terminal แบบ GUI ได้ทั้งหมด โดยไม่ต้องจำ CLI commands หรือ curl

**ทำไม Textual?**
1. สร้างบน Rich ที่ project ใช้อยู่แล้ว (benchmark runners ทุกตัวใช้ Rich)
2. Python-native — ใช้ `uv` ได้เลย ไม่ต้อง stack ใหม่
3. Async-first — match กับ FastAPI async patterns
4. Built-in widgets ที่ต้องใช้: DataTable, Input, TextLog, Tree, TabbedContent, ModalScreen

---

## Requirements

- Interactive RAG chat พร้อม login (4 user types) และดู retrieved chunks พร้อม scores
- Dashboard แสดง system status: connection, user, Docker, API keys
- Benchmark runner สำหรับทุก phase (vector-db, rag-framework, embedding-model, llm-provider) พร้อม real-time output
- Benchmark result viewer — อ่าน JSON results ที่มีอยู่แล้วและแสดงเป็นตาราง
- Document management (upload, search, view collections) ตาม RBAC
- Integration test runner พร้อม pass/fail status
- Settings panel สำหรับ configure API URL, keys, parameters
- ทำงานได้ 2 mode: **HTTP mode** (เรียก API server) และ **Embedded mode** (import FastAPI app ตรง)

---

## Architecture

### New Directory: `tui/`

```
tui/
  __init__.py
  __main__.py                 # Entry point: python -m tui
  app.py                      # Main RAGTuiApp(App) class
  config.py                   # TUISettings (pydantic-settings)
  client.py                   # RAGClient + EmbeddedRAGClient (httpx)

  screens/
    __init__.py
    dashboard.py              # Home: status overview, quick actions
    chat.py                   # Interactive RAG chat
    benchmarks.py             # Benchmark runner (4 tabs by phase)
    results.py                # Benchmark result viewer
    documents.py              # Document management
    settings.py               # Settings & configuration
    tests.py                  # Integration test runner

  widgets/
    __init__.py
    chat_message.py           # Chat bubble widget (user/assistant)
    chunk_viewer.py           # Retrieved chunks display with scores
    benchmark_progress.py     # Progress bar + live log
    result_table.py           # DataTable wrapper for benchmark results
    login_dialog.py           # Modal login dialog
    status_bar.py             # Bottom status bar (user, connection, phase)

  styles/
    app.tcss                  # Textual CSS stylesheet
```

### Modified Files

| File | Change |
|------|--------|
| `pyproject.toml` | เพิ่ม dependency group `tui` |
| `Makefile` | เพิ่ม `make install-tui` และ `make tui` targets |

---

## Implementation Phases

---

### Phase 1: Foundation & Shell (MVP)

**เป้าหมาย**: App structure + navigation + login + basic chat

#### Step 1.1 — Add TUI dependencies (`pyproject.toml`)

เพิ่ม dependency group ใหม่:

```toml
# ── Phase 6: TUI ─────────────────────────────────────────────────────────────
tui = [
    { include-group = "api" },
    "textual>=0.80.0",
    "httpx>=0.28.0",
]
```

`include-group = "api"` เพราะ embedded mode ต้อง import FastAPI app ตรง

#### Step 1.2 — App shell (`tui/app.py`, `tui/__main__.py`)

- `__main__.py`: `RAGTuiApp().run()`
- `app.py`: Textual `App` subclass:
  - Header + Footer
  - Sidebar navigation (Tree/ListView): Dashboard, Chat, Benchmarks, Results, Documents, Tests, Settings
  - Screen switching ด้วย `push_screen()` / `switch_screen()`
  - Global keybindings: `q`=quit, `ctrl+p`=command palette, `F1`-`F7`=jump to screens, `escape`=back

#### Step 1.3 — HTTP client (`tui/client.py`)

Class `RAGClient` wrapping `httpx.AsyncClient`:

| Method | Endpoint |
|--------|----------|
| `login(username, password) -> str` | POST `/api/v1/auth/token` |
| `chat(messages, top_k, collection) -> dict` | POST `/api/v1/chat/completions` |
| `search(query, top_k) -> dict` | GET `/api/v1/documents/search` |
| `upload(content, filename, access_level) -> dict` | POST `/api/v1/documents/upload` |
| `me() -> dict` | GET `/api/v1/me` |
| `submit_feedback(query_id, rating, comment) -> dict` | POST `/api/v1/feedback` |
| `health_check() -> bool` | GET `/` |

Error handling ทุก case: connection refused, 401, 403, 503

#### Step 1.4 — TUI config (`tui/config.py`)

```python
class TUISettings(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    embedded_mode: bool = False   # True = ASGITransport (no server needed)
    theme: str = "dark"
    default_user: str = ""        # auto-login
    default_password: str = ""
    model_config = {"env_file": ".env", "env_prefix": "TUI_", "extra": "ignore"}
```

Config ผ่าน `.env`: `TUI_API_BASE_URL`, `TUI_EMBEDDED_MODE`, etc.

#### Step 1.5 — Login dialog (`tui/widgets/login_dialog.py`)

Modal screen (`ModalScreen`) with:
- Username Input + Password Input (password masked)
- 4 quick-login buttons: `alice_admin`, `bob_employee`, `carol_customer`, `svc_line_bot` (PoC convenience)
- Login button → calls `RAGClient.login()`
- Error display on failure
- On success: dismiss modal, update status bar

#### Step 1.6 — Dashboard screen (`tui/screens/dashboard.py`)

Landing page แสดง:
- Connection status (green/red indicator + latency)
- Current user info (username, type, permissions list)
- API key status (OPENROUTER, OPENAI, ANTHROPIC, COHERE)
- Docker container status (vector DBs)
- Quick action buttons: Start Chat, Run Benchmarks, View Results, Run Tests
- Recent benchmark results summary (read from JSON files)

#### Step 1.7 — Chat screen (`tui/screens/chat.py`)

Layout:
- **Message history** (ScrollableContainer): chat messages ด้านบน
- **Chunk viewer** (collapsible sidebar): retrieved chunks พร้อม scores และ access_level badges
- **Input bar** (bottom): Input + Send button + settings icon

`ChatMessage` widget:
- User messages: right-aligned, blue background
- Assistant messages: left-aligned, green background, แสดง model name + token usage
- Thumbs up/down buttons → calls `submit_feedback()`

`ChunkViewer` widget:
- แต่ละ chunk: title, score bar, access_level badge, content preview
- Click chunk → expand to full content

Settings sidebar (collapsible): top_k slider, collection dropdown

#### Step 1.8 — Stylesheet (`tui/styles/app.tcss`)

Textual CSS (.tcss) สำหรับ:
- Dark/light color scheme
- Sidebar width + styling
- Chat bubble styles (user vs assistant)
- DataTable alternating rows
- Modal dialog
- Access level badges: green (customer_kb) / yellow (internal_kb) / red (confidential_kb)
- Progress bars

#### Step 1.9 — Makefile targets

```makefile
# ── Phase 6: TUI ─────────────────────────────────────────────────────────────
install-tui:
	$(UV) sync --group tui

tui:
	$(UV) run python -m tui

tui-embedded:
	TUI_EMBEDDED_MODE=true $(UV) run python -m tui
```

---

### Phase 2: Benchmark Runner & Result Viewer

**เป้าหมาย**: รัน benchmarks ทุก phase จาก TUI พร้อม real-time output + ดู results เป็นตาราง

#### Step 2.1 — Benchmark runner screen (`tui/screens/benchmarks.py`)

`TabbedContent` with 4 tabs:

**Vector DB tab**:
- Checkboxes: qdrant, pgvector, milvus, opensearch
- Number input: n_vectors (default 10,000)
- Prerequisite check: Docker containers running
- Run → executes `benchmarks/vector-db/run_benchmark.py` via subprocess

**RAG Framework tab**:
- Checkboxes: bare_metal, llamaindex, langchain, haystack
- Toggle: --no-llm mode
- Status: OPENROUTER_API_KEY required indicator
- Run → executes `benchmarks/rag-framework/evaluate.py`

**Embedding Model tab**:
- Checkboxes: bge_m3, multilingual_e5, mxbai, wangchanberta, openai_large, openai_small, cohere_v3
- Number input: top_k
- Status: API key status per model
- Run → executes `benchmarks/embedding-model/evaluate.py`

**LLM Provider tab**:
- Checkboxes: ทุก providers (11 ตัว)
- Number input: top_k
- Status: API key status per provider
- Run → executes `benchmarks/llm-provider/evaluate.py`

`BenchmarkProgress` widget:
- `RichLog` widget สำหรับ real-time output
- Cancel button → sends SIGTERM to subprocess
- Status: idle / running / done / error

**หมายเหตุ**: รัน subprocess ด้วย `FORCE_COLOR=0` เพื่อ strip ANSI codes ก่อน feed เข้า RichLog. ใช้ Textual `Worker` pattern (`self.run_worker()`) เพื่อไม่ block UI

#### Step 2.2 — Result viewer screen (`tui/screens/results.py`)

`TabbedContent` with 4 tabs:

**Vector DB results** (อ่านจาก `benchmarks/vector-db/results/*.json`):
- Columns: DB, Vectors, Index Time, Throughput, p50/p95/p99 latency, QPS, Filter p95, Recall@10

**RAG Framework results** (อ่านจาก `benchmarks/rag-framework/results/*.json`):
- Indexing table: Framework, Chunks, Index Time, LOC
- Query latency table: Framework, Min, Avg, Max, p95
- Click row → ดู question + answer + sources

**Embedding Model results** (อ่านจาก `benchmarks/embedding-model/results/*.json`):
- Retrieval quality: Model, Thai Recall, Eng Recall, Overall, MRR
- Latency & cost: Index Time, Query Avg, Cost/1M, Self-hosted
- Scorecard: Rank, Model, Weighted Score, Verdict

**LLM Provider results** (อ่านจาก `benchmarks/llm-provider/results/*.json`):
- Answer quality: Provider, Overall F1, Thai F1, Questions
- Cost & latency: Avg Latency, Total Cost, $/1M in, $/1M out
- Scorecard: Rank, Provider, Weighted Score, Verdict

---

### Phase 3: Document Management & Test Runner

**เป้าหมาย**: CRUD documents ผ่าน TUI + รัน integration tests

#### Step 3.1 — Document management screen (`tui/screens/documents.py`)

3 sections:
1. **Search**: Input + results DataTable (doc_id, title, access_level, score, content preview)
2. **Upload**: File path input + access_level RadioSet + Upload button (employee/admin only)
3. **Collections**: access levels ที่ user เห็นได้ + total visible docs

#### Step 3.2 — Integration test runner screen (`tui/screens/tests.py`)

Tree view of test scenarios (7 scenarios, 27 tests):
- Scenario 1: Employee Upload & Query (4 tests)
- Scenario 2: Customer Permission Filter (5 tests)
- Scenario 3: LINE Webhook E2E (4 tests)
- Scenario 4: Concurrent Queries (2 tests)
- Scenario 5: Component Swap (3 tests)
- Scenario 6: Error Handling (5 tests)
- Scenario 7: Thai Language E2E (4 tests)

Features:
- Checkbox per scenario
- "Run Selected" / "Run All" buttons
- Execute: `uv run pytest tests/integration/ -v --tb=short -k "TestScenarioN"`
- RichLog: real-time test output
- Summary: passed/failed/skipped counts (green/red)

---

### Phase 4: Polish & Advanced Features

**เป้าหมาย**: Settings, embedded mode, keyboard shortcuts

#### Step 4.1 — Settings screen (`tui/screens/settings.py`)

Sections:
1. **Connection**: API URL input, embedded mode toggle, "Test Connection" button
2. **API Keys**: แสดง status ของทุก key (masked หรือ "not set")
3. **Models**: LLM model, embedding model, chunk size/overlap, top_k
4. **Docker**: status ของ vector DB containers (parse `docker compose ps`)
5. **Theme**: Dark/Light toggle

Read from `.env` file, write changes back พร้อม format preservation

#### Step 4.2 — Embedded mode (`tui/client.py`)

เพิ่ม `EmbeddedRAGClient` class:
```python
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from api.main import app

class EmbeddedRAGClient(RAGClient):
    def __init__(self):
        transport = ASGITransport(app=app)
        self._http = AsyncClient(transport=transport, base_url="http://test")
```

TUI app เลือก client ตาม `TUI_EMBEDDED_MODE`:
- `False` (default): `RAGClient("http://localhost:8000")`
- `True`: `EmbeddedRAGClient()` — ไม่ต้องรัน API server แยก

#### Step 4.3 — Command palette & keybindings (`tui/app.py`)

Textual CommandPalette (Ctrl+P) commands:
- "Chat: New conversation"
- "Benchmark: Run Vector DB (quick)"
- "Benchmark: Run RAG Framework"
- "Benchmark: Run Embedding Models"
- "Benchmark: Run LLM Providers"
- "Results: View latest"
- "Tests: Run all integration tests"
- "Login as admin / employee / customer"
- "Settings: Open"

Global keybindings: `ctrl+l`=clear chat, `ctrl+n`=new chat session, `escape`=back

#### Step 4.4 — Status bar (`tui/widgets/status_bar.py`)

Custom Footer showing:
- Left: Current user (icon + username + type badge)
- Center: Connection status (green "Connected" / red "Disconnected")
- Right: Active benchmark status หรือ current screen name

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Textual API changes (pre-1.0) | Medium | Pin `>=0.80.0,<1.0.0`. ใช้ stable APIs เท่านั้น |
| Benchmark subprocess blocks UI | High | ใช้ Textual `Worker` pattern. Add cancel button (SIGTERM) |
| ANSI escape codes ใน subprocess output | Medium | Run subprocess with `FORCE_COLOR=0` |
| Thai text word-wrap | Low | Textual/Rich handle Unicode width correctly |
| Embedded mode ASGI lifecycle | Medium | httpx `ASGITransport` handles this. Test thoroughly |
| Large result JSON files | Low | Lazy-load DataTable rows, pagination for details |

---

## Dependencies

**New (external)**:
- `textual>=0.80.0` — TUI framework (pulls Rich automatically)
- `httpx>=0.28.0` — async HTTP client (already in `api` group)

**Existing (reused, no changes)**:
- `api/` — FastAPI app for embedded mode
- `benchmarks/*/evaluate.py` — called via subprocess
- `benchmarks/*/results/*.json` — read for result viewer
- `rich` — already installed

---

## File Summary

| File | Phase | New/Modified |
|------|-------|-------------|
| `pyproject.toml` | 1.1 | Modified |
| `Makefile` | 1.9 | Modified |
| `tui/__init__.py` | 1.2 | New |
| `tui/__main__.py` | 1.2 | New |
| `tui/app.py` | 1.2 | New |
| `tui/config.py` | 1.4 | New |
| `tui/client.py` | 1.3 | New |
| `tui/screens/dashboard.py` | 1.6 | New |
| `tui/screens/chat.py` | 1.7 | New |
| `tui/screens/benchmarks.py` | 2.1 | New |
| `tui/screens/results.py` | 2.2 | New |
| `tui/screens/documents.py` | 3.1 | New |
| `tui/screens/tests.py` | 3.2 | New |
| `tui/screens/settings.py` | 4.1 | New |
| `tui/widgets/login_dialog.py` | 1.5 | New |
| `tui/widgets/chat_message.py` | 1.7 | New |
| `tui/widgets/chunk_viewer.py` | 1.7 | New |
| `tui/widgets/benchmark_progress.py` | 2.1 | New |
| `tui/widgets/result_table.py` | 2.2 | New |
| `tui/widgets/status_bar.py` | 4.4 | New |
| `tui/styles/app.tcss` | 1.8 | New |

**Total: 2 modified + 19 new files**

---

## Success Criteria

- [ ] `make install-tui && make tui` starts without errors
- [ ] Login ด้วย 4 users ทุกคนได้
- [ ] Chat ด้วย Thai + English query เห็น RAG response + retrieved chunks พร้อม scores
- [ ] Benchmark runner รัน benchmark ทุก phase ได้ พร้อม real-time output
- [ ] Result viewer โหลด JSON results ทุก 4 types แสดงเป็นตาราง
- [ ] Document search กรองตาม user permissions
- [ ] Employee/admin upload documents ได้, customer ไม่ได้
- [ ] Integration test runner แสดง pass/fail status
- [ ] Embedded mode (`make tui-embedded`) ทำงานได้โดยไม่ต้องรัน server แยก
- [ ] Long-running benchmarks ยกเลิกได้โดยไม่ freeze UI
- [ ] Thai text แสดงผลถูกต้องตลอด application

---

## Effort Estimate

| Phase | Description | Complexity | Estimate |
|-------|-------------|------------|----------|
| 1 | Foundation & Shell | Medium | 2-3 days |
| 2 | Benchmarks & Results | Medium | 1-2 days |
| 3 | Documents & Tests | Low | 1 day |
| 4 | Polish & Advanced | Medium | 1-2 days |
| **Total** | | | **5-8 days** |

---

## Next Step

ยืนยัน plan แล้ว → เริ่ม Phase 1 ด้วย Step 1.1 (pyproject.toml) และ Step 1.2 (app shell) พร้อมกัน

**WAITING FOR CONFIRMATION**: พร้อม proceed กับ plan นี้ไหม? (yes / modify / skip to phase N)
