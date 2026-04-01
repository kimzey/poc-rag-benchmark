<!-- Generated: 2026-04-01 | Files scanned: 54 | Token estimate: ~350 -->

# RAG Spike Codemaps — Index

**Last Updated:** 2026-04-01 (Updated: Phase 6 Phase 2 - Benchmarks & Results screens)  
**Total Modules:** 54 files scanned  
**Phases:** 1-6 (complete stack: benchmarks → API → TUI, Phase 6 Phase 2 complete)

## Quick Navigation

| Codemap | Phase(s) | Focus | Size |
|---------|----------|-------|------|
| **[architecture.md](architecture.md)** | All (1-6) | Overall 6-phase structure, data flow, design patterns | ~800 tokens |
| **[backend.md](backend.md)** | 4 | FastAPI routes, auth middleware, RBAC, RAG pipeline | ~650 tokens |
| **[tui.md](tui.md)** | 6 | Textual TUI app, screens (Phase 1-2 complete), widgets, navigation | ~850 tokens |
| **[benchmarks.md](benchmarks.md)** | 1-3.5 | ABC base classes, 4 vector DBs, 4 RAG frameworks, 6 embedding models, 4 LLM providers | ~750 tokens |
| **[dependencies.md](dependencies.md)** | All | uv dependency groups, Docker services, API keys, configuration | ~600 tokens |

## What Each Phase Does

### Phase 1: Vector DB Benchmark (`benchmarks/vector-db/`)

Compares 4 vector databases:
- **Qdrant** — Modern, fully open-source, excellent filtering
- **pgvector** — PostgreSQL extension, already using DB
- **Milvus** — Scalable, Chinese-built, good for distributed
- **OpenSearch** — Open-source Elasticsearch fork, built-in analytics

**Metrics:** Insert/search latency (p50/p95/p99), QPS, recall@10  
**CLI:** `make benchmark-quick` (10K vectors) or `make benchmark-scale` (100K vectors)

### Phase 2: RAG Framework Benchmark (`benchmarks/rag-framework/`)

Compares 4 RAG orchestration frameworks:
- **bare_metal** — Minimal, no framework overhead
- **LlamaIndex** — Clean API, strong community
- **LangChain** — Most popular, many integrations
- **Haystack** — DAG-based, good for pipelines

**Metrics:** Indexing time, query latency, LOC (code complexity)  
**CLI:** `make rag-eval` (requires OPENROUTER_API_KEY)

### Phase 3: Embedding Model Benchmark (`benchmarks/embedding-model/`)

Compares 6 embedding models (2 open + 4 commercial):
- Open: BGE-M3 (multilingual), E5-Multilingual, MxBai, WangchanBERTa (Thai)
- Commercial: OpenAI (3-small/3-large), Cohere V3

**Metrics:** Thai/English recall@k, MRR, latency, cost, self-hostability, vendor lock-in  
**CLI:** `make embed-eval` (open models only) or with `--use-paid` for commercial models

### Phase 3.5: LLM Provider Benchmark (`benchmarks/llm-provider/`)

Compares 4 LLM providers & 10+ models:
- **OpenRouter** — 6 models through unified API (best value)
- **OpenAI Direct** — GPT-4o, GPT-4o-mini (most capable)
- **Anthropic Direct** — Claude 3.5 Sonnet, Claude 3 Haiku (best reasoning)
- **Ollama** — Self-hosted llama3.1 (free, private)

**Metrics:** Answer quality (F1), latency, cost, lock-in, reliability  
**CLI:** `make llm-eval` (requires API keys)

### Phase 4: RAG API Server (`api/`)

Production-ready FastAPI server with:
- **Auth:** JWT tokens, 4 user types (admin/employee/customer/service)
- **RBAC:** 8 permissions (doc:read/upload/delete/index, chat:query, user:manage, system:config, analytics:read)
- **Permission-Filtered Retrieval:** Documents tagged with access_level (customer_kb, internal_kb, confidential_kb)
- **RAG Pipeline:** Retrieve → Prompt → LLM (OpenRouter or mock)
- **Webhooks:** LINE Messaging API adapter

**Endpoints:** 9 routes under `/api/v1`  
**CLI:** `make api-run` → http://localhost:8000/docs

### Phase 5: Integration Tests (`tests/`)

Comprehensive end-to-end testing:
- **pytest:** 27 tests across 7 scenarios (E2E, RBAC, Thai language, error handling)
- **Locust:** Load testing (employees 3x weight, customers 1x weight)

**Metrics:** p50/p95 latency < 3s/8s, throughput > 50 req/sec  
**CLI:** `make test-integration` (no server needed) or `make load-test`

### Phase 6: Textual TUI (`tui/`)

Terminal user interface for interactive exploration — Phase 2 complete:
- **Phase 1 (Complete):** Dashboard — System status, Chat — Message history + retrieval
- **Phase 2 (Complete):** Benchmarks — Run 4 benchmark types, Results — View benchmark metrics
- **Navigation** — F1-F7 keybindings, Login dialog, async subprocess streaming
- **Widgets:** BenchmarkProgress (real-time output), ResultTable (DataTable wrapper)

**Requires:** Running API server on localhost:8000  
**CLI:** `make tui` or `python -m tui`

## Architecture Patterns

### Port & Adapter (Phase 1-3.5)

Each benchmark phase uses:
1. **ABC Base Class** — Defines interface (VectorDBClient, BaseRAGPipeline, etc.)
2. **Concrete Adapters** — One per vendor/framework
3. **Evaluator** — Swaps implementations, compares metrics

**Benefit:** Add new component = 1 file, zero evaluator changes

### RBAC + Permission Filtering (Phase 4)

- **RBAC Table:** UserType → Set[Permission] defined at module load
- **Access Level Matrix:** UserType → Set[AccessLevel] (who sees what)
- **Retrieval Filter:** Applied BEFORE scoring (not post-hoc)

**Benefit:** Security at data level, not presentation layer

### Async/Await (Phase 4, 6)

- FastAPI routes: async functions with `async def`
- TUI: httpx.AsyncClient for non-blocking API calls
- LLM calls: AsyncOpenAI for concurrent requests

**Benefit:** Non-blocking I/O, better throughput

## Setup Checklist

```bash
# 1. Prerequisites
python --version              # ≥ 3.11
uv --version                  # or: pip install uv

# 2. Initial setup
make setup                    # Checks prereqs, creates .env
# Edit .env with your API keys (see dependencies.md)

# 3. Install phase(s) you need
make install                  # Phase 1 only (fast, ~500MB)
make install-api              # Phase 4 (for server dev)
make install-test             # Phase 5 (includes Phase 4)

# 4. Start infrastructure (if benchmarking Phase 1)
make up-db                    # Docker: Qdrant, pgvector, Milvus, OpenSearch

# 5. Run
make api-run                  # API server
make tui                      # TUI client
make test-integration         # Tests
```

## Key Files by Responsibility

| Task | File(s) |
|------|---------|
| Add new vector DB | `benchmarks/vector-db/mynewdb/client.py` |
| Add new RAG framework | `benchmarks/rag-framework/frameworks/myfw/pipeline.py` |
| Add new embedding model | `benchmarks/embedding-model/mymodel/model.py` |
| Add new LLM provider | `benchmarks/llm-provider/myprovider/provider.py` |
| Add new API endpoint | `api/routes/myroute.py` + register in `api/main.py` |
| Add new TUI screen | `tui/screens/myscreen.py` + register in `tui/app.py` ContentSwitcher + add NavButton |
| Change auth rules | `api/auth/models.py` (ROLE_PERMISSIONS, USER_ACCESS_LEVELS) |
| Configure dependencies | `pyproject.toml` (modify `[dependency-groups]`) |

## Environment Variables

See **[dependencies.md](dependencies.md#configuration-files)** for:
- `.env` template (`cp .env.example .env`)
- Sections: API, OpenAI, Anthropic, Cohere, Ollama, TUI

## Related Documentation

- **CLAUDE.md** — Project overview, commands, architecture
- **SETUP.md** — Detailed setup instructions (Docker, virtual env, API keys)
- **plan.md** — Full 6-phase spike plan with design decisions
- **README.md** — Quick start, feature list

## Document Maintenance

These codemaps are **generated from the codebase** and updated regularly:
- Last scanned: 2026-04-01 (Updated for TUI Phase 2: Benchmarks & Results)
- Files scanned: 50+ (added: tui/screens/benchmarks.py, tui/screens/results.py, tui/widgets/benchmark_progress.py, tui/widgets/result_table.py)
- Coverage: All 6 phases (100%) — Phase 6 Phase 2 now complete
- Token total: ~3,650 tokens (6 codemaps, tui.md expanded to ~850 tokens)

**To regenerate:** See instructions in CONTRIBUTING.md (section "Generate Codemaps")
