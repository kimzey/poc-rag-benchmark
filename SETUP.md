# spike-rak — Setup & Usage Guide

Environment management ใช้ **[uv](https://docs.astral.sh/uv/)** — Python package manager ที่เร็วกว่า pip ~10-100x  
แต่ละ phase install deps แยกกันผ่าน dependency groups ใน `pyproject.toml`

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.11 | `brew install python` |
| uv | ≥ 0.5 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | any | [docker.com](https://www.docker.com/) — Phase 1 only |

ตรวจสอบ:
```bash
uv --version   # uv 0.10.x
python3 --version  # Python 3.11+
docker --version   # Phase 1 only
```

---

## First-time Setup

```bash
git clone <repo>
cd spike-rak

# 1. Copy .env และกรอก API keys
cp .env.example .env

# 2. ตรวจสอบ setup
make setup
```

`make setup` จะ:
- ตรวจว่า uv ติดตั้งแล้ว
- สร้าง `.env` จาก `.env.example` (ถ้ายังไม่มี)
- แสดง quick-start commands

> `.venv/` จะถูกสร้างอัตโนมัติเมื่อ run `make install-*` ครั้งแรก — ไม่ต้อง activate เอง

---

## Environment Overview

```
pyproject.toml               ← แหล่งความจริงเดียวสำหรับ deps ทุก phase
uv.lock                      ← lockfile (commit ไว้ — reproducible builds)
.venv/                       ← virtual env เดียว managed by uv (gitignored)
```

**Dependency Groups:**

| Group | Phase | ขนาดประมาณ | คำสั่ง |
|-------|-------|------------|--------|
| `bench-vectordb` | 1 | ~150MB | `make install` |
| `bench-rag` | 2 | ~2GB (torch) | `make install-rag` |
| `bench-embed` | 3 | ~1.5GB (torch) | `make install-embed` |
| `bench-llm` | 3.5 | ~50MB | `make install-llm` |
| `api` | 4 | ~80MB | `make install-api` |
| `test` | 5 | ~80MB + api | `make install-test` |

> `uv sync --group <name>` จะ switch venv ให้ตรงกับ group นั้น (deps อื่นถูกลบ)  
> ถ้าต้องการ install หลาย group พร้อมกัน: `uv sync --group api --group test`

---

## Phase 1 — Vector DB Benchmarks

### Setup
```bash
# Start Vector DBs (Docker required)
make up-db           # start all: qdrant, pgvector, milvus, opensearch
make up-db DB=qdrant # start single DB only

# Install deps
make install         # uv sync --group bench-vectordb
```

### Run Benchmarks
```bash
make benchmark-quick     # 10K vectors
make benchmark-medium    # 100K vectors
make benchmark-all       # 10K + 100K (sequential)

# Single DB only
make benchmark-db DB=qdrant N=50000

# Check status / logs
make ps-db
make logs-db DB=qdrant
```

### Stop
```bash
make down-db    # stop + remove volumes
```

### ENV vars needed
```bash
# .env — ไม่ต้องมี API key สำหรับ Phase 1
# Vector DBs ทำงานแบบ local ผ่าน Docker
```

---

## Phase 2 — RAG Framework Comparison

> ⚠️ ต้องการ ~2GB disk (torch + llama-index + langchain + haystack)

### Setup
```bash
make install-rag    # uv sync --group bench-rag
```

### Run
```bash
# ต้องการ OPENROUTER_API_KEY ใน .env
make rag-eval                        # run all 4 frameworks
make rag-eval-framework F=llamaindex # run single framework
make rag-eval-framework F=langchain
make rag-eval-framework F=haystack
make rag-eval-framework F=bare_metal

# ไม่มี API key — run indexing only
make rag-eval-no-llm
```

### ENV vars needed
```bash
OPENROUTER_API_KEY=sk-or-...
RAG_LLM_MODEL=openai/gpt-4o-mini  # default
```

---

## Phase 3 — Embedding Model Comparison

> ⚠️ ต้องการ ~1.5GB disk + model download ครั้งแรก (~1GB เก็บใน `.cache/`)

### Setup
```bash
make install-embed    # uv sync --group bench-embed
```

### Run
```bash
# Open-source models (ไม่ต้องการ API key)
make embed-eval                          # run default models

# All models รวม OpenAI (ต้องการ OPENAI_API_KEY)
make embed-eval-all

# Single model
make embed-eval-model M=bge_m3
make embed-eval-model M=multilingual_e5
make embed-eval-model M=mxbai
make embed-eval-model M=openai_large    # requires OPENAI_API_KEY
make embed-eval-model M=openai_small    # requires OPENAI_API_KEY

# Override top-k
make embed-eval-topk K=5
```

### ENV vars needed
```bash
OPENAI_API_KEY=sk-...    # optional — open-source models ไม่ต้องการ
```

---

## Phase 3.5 — LLM Provider Comparison

### Setup
```bash
make install-llm    # uv sync --group bench-llm
```

### Run
```bash
make llm-eval                       # default: openrouter gpt-4o-mini
make llm-eval-all                   # all configured providers
make llm-eval-provider P=openrouter
make llm-eval-provider P=openai
make llm-eval-topk K=5
```

### ENV vars needed
```bash
OPENROUTER_API_KEY=sk-or-...
# OPENAI_API_KEY=sk-...      # optional
# ANTHROPIC_API_KEY=sk-...   # optional
```

---

## Phase 4 — API Server

### Setup
```bash
make install-api    # uv sync --group api
```

### Run
```bash
# Start server
make api-run
# → http://localhost:8000/docs  (Swagger UI)
# → http://localhost:8000/redoc (ReDoc)

# Smoke test (ไม่ต้องการ API key — ใช้ mock LLM)
make api-demo
```

### Test Users (built-in)
| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `alice_admin` | `admin123` | admin | all |
| `bob_employee` | `emp123` | employee | doc:read, doc:upload, doc:index, chat:query |
| `carol_customer` | `cust123` | customer | doc:read, chat:query |
| `svc_line_bot` | `svc123` | service | doc:read, chat:query |

### Quick curl test
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"bob_employee","password":"emp123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# RAG query
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"นโยบายการลาพักร้อน?"}],"top_k":3}'
```

### ENV vars needed
```bash
# ไม่มี API key → ใช้ mock LLM response อัตโนมัติ
OPENROUTER_API_KEY=sk-or-...   # optional — เปิดใช้ real LLM
OPENROUTER_MODEL=openai/gpt-4o-mini

# LINE Messaging API (optional)
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

---

## Phase 5 — Integration Tests & Load Tests

### Setup
```bash
make install-test   # uv sync --group test  (includes api group automatically)
```

### Run Integration Tests
```bash
# Run all 27 tests (7 scenarios)
make test-integration

# Verbose output (full tracebacks)
make test-integration-verbose

# Run single scenario class
uv run pytest tests/integration/ -v -k "TestScenario1"
uv run pytest tests/integration/ -v -k "TestScenario6"  # LLM error handling

# Run with specific marker or test name
uv run pytest tests/integration/test_scenarios.py::TestScenario7ThaiLanguageE2E -v
```

### Test Scenarios
| # | Class | Covers |
|---|-------|--------|
| 1 | `TestScenario1EmployeeUploadAndQuery` | Upload → index → query |
| 2 | `TestScenario2CustomerPermissionFilter` | Access control / RBAC |
| 3 | `TestScenario3LineWebhookE2E` | LINE adapter → RAG pipeline |
| 4 | `TestScenario4ConcurrentQueries` | 30 concurrent requests |
| 5 | `TestScenario5ComponentSwap` | Retrieval abstraction layer |
| 6 | `TestScenario6LLMErrorHandling` | Timeout → 503, recovery |
| 7 | `TestScenario7ThaiLanguageE2E` | Thai queries end-to-end |

### Run Load Tests (Locust)
```bash
# Terminal 1: start API server
make api-run

# Terminal 2: run load test
make load-test               # 50 users, 5/s ramp, 30s
make load-test U=100 R=10 T=60s  # custom params

# Interactive UI mode (Locust dashboard)
uv run locust -f tests/load/locustfile.py --host=http://localhost:8000
# → http://localhost:8089
```

**Performance Targets (from plan):**

| Metric | Target |
|--------|--------|
| E2E latency p50 | < 3s |
| E2E latency p95 | < 8s |
| Retrieval latency p95 | < 200ms |
| Throughput | > 50 req/s |

---

## .env Reference

```bash
# .env.example — copy to .env and fill in values

# ── Phase 2-3.5: LLM & Embeddings ─────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-...          # https://openrouter.ai
RAG_LLM_MODEL=openai/gpt-4o-mini
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3

# ── Phase 3: Embedding (optional — OpenAI models only) ────────────────────────
OPENAI_API_KEY=sk-...

# ── Phase 3.5: LLM Providers (optional) ───────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# ── Phase 4-5: API Server ─────────────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-...          # same key as above
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ── Phase 4: LINE Webhook (optional) ──────────────────────────────────────────
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

---

## Common Patterns

### ทำงานโดยไม่ต้อง activate venv
```bash
# uv run จัดการให้อัตโนมัติ
uv run python <script.py>
uv run pytest tests/
uv run uvicorn api.main:app --reload
```

### Activate venv แบบ manual (ถ้าต้องการ)
```bash
source .venv/bin/activate
python ...
deactivate
```

### Switch ระหว่าง phases
```bash
# ถ้าจะ switch จาก api → bench-rag
make install-rag     # uv sync --group bench-rag
# venv จะถูก update ให้ตรงกับ bench-rag

# ถ้าต้องการ api + test พร้อมกัน
uv sync --group api --group test
```

### Add dependency ใหม่
```bash
# เพิ่มใน pyproject.toml แล้ว sync
# หรือใช้ uv add
uv add --group api "some-package>=1.0"
uv add --group test "pytest-cov"
```

### Check installed packages
```bash
uv pip list
uv pip show fastapi
```

---

## Troubleshooting

**`uv: command not found`**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv
source $HOME/.local/bin/env  # restart shell or source profile
```

**`ModuleNotFoundError` after switching groups**
```bash
# Re-sync ให้ตรงกับ phase ที่ใช้
make install-api     # หรือ group ที่ต้องการ
```

**Port 8000 already in use**
```bash
lsof -ti:8000 | xargs kill -9
make api-run
```

**Docker not running (Phase 1)**
```bash
open -a Docker   # macOS — start Docker Desktop
make up-db
```

**Model download slow (Phase 2-3)**
```bash
# Models เก็บใน .cache/ — download ครั้งเดียว
# ครั้งแรกอาจใช้เวลา 5-15 นาที ขึ้นอยู่กับขนาด model
```
