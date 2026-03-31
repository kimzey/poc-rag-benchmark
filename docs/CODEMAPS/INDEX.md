<!-- Generated: 2026-03-31 | Files scanned: 76 | Token estimate: ~520 -->

# RAG Spike Codemaps Index

**Last Updated:** 2026-03-31 | **Project Phase:** 1 ✅ Vector DB | 2 🔄 RAG Framework | 3 🔄 Embedding Models | 3.5 🆕 LLM Providers | 4 🆕 API Layer | 5 🆕 Integration Testing | 6 🔄 RFC & Docs

## Quick Navigation

| Codemap | Read When |
|---------|-----------|
| [architecture.md](./architecture.md) | Understanding system design, Port & Adapter pattern, entry points, all phases |
| [data.md](./data.md) | Data schemas (BenchmarkRecord, RAGResult, EmbedResult), dataset contents |
| [dependencies.md](./dependencies.md) | Python packages, Docker stack, Makefile targets, env vars, embedding models |

---

## Project Structure

```
spike-rak/
├── plan.md                                  # 6-phase spike plan
├── SETUP.md                                 # Full usage & setup guide for all phases
├── pyproject.toml                           # Root project (uv dependency groups)
├── uv.lock                                  # Lockfile (reproducible installs)
├── Makefile                                 # make <phase-target> wraps uv
├── .env.example                             # Environment variables template
├── .gitignore                               # Updated: .venv-*/ pattern
│
├── docker/
│   └── docker-compose.vector-db.yml        # 6 services (Qdrant, PG, Milvus, OpenSearch + deps)
│
├── datasets/                               # Phase 2 real-world documents
│   ├── hr_policy_th.md                    # HR policy (Thai)
│   ├── tech_docs_en.md                    # API docs (English)
│   ├── faq_mixed.md                       # FAQ (Thai + English mixed)
│   └── questions.json                     # 10 test questions (4 categories)
│
├── benchmarks/
│   ├── vector-db/                         # [Phase 1 ✅]
│   │   ├── run_benchmark.py               # Orchestrator
│   │   ├── requirements.txt
│   │   ├── clients/
│   │   │   ├── base.py                   # VectorDBClient ABC
│   │   │   ├── qdrant.py
│   │   │   ├── pgvector.py
│   │   │   ├── milvus.py
│   │   │   └── opensearch.py
│   │   ├── utils/
│   │   │   ├── dataset.py               # Synthetic data, ground truth
│   │   │   └── metrics.py               # LatencyStats, recall
│   │   └── results/                     # Timestamped JSON outputs
│   │
│   ├── rag-framework/                    # [Phase 2 🔄]
│   │   ├── evaluate.py                   # Comparison runner
│   │   ├── base.py                       # BaseRAGPipeline ABC
│   │   ├── config.py                     # .env → settings
│   │   ├── requirements.txt
│   │   ├── frameworks/
│   │   │   ├── bare_metal/pipeline.py   # numpy + direct OpenRouter
│   │   │   ├── llamaindex_poc/pipeline.py
│   │   │   ├── langchain_poc/pipeline.py
│   │   │   └── haystack_poc/pipeline.py
│   │   └── results/                     # rag_framework_results.json
│   │
│   ├── embedding-model/                  # [Phase 3 🔄]
│   │   ├── evaluate.py                   # Retrieval quality + weighted scorecard
│   │   ├── base.py                       # BaseEmbeddingModel ABC
│   │   ├── config.py                     # Chunk settings, paths
│   │   ├── requirements.txt
│   │   ├── models/
│   │   │   ├── bge_m3.py                # BAAI/bge-m3 (multilingual)
│   │   │   ├── multilingual_e5.py       # intfloat/multilingual-e5-large
│   │   │   ├── mxbai.py                 # mixedbread-ai/mxbai-embed-large-v1
│   │   │   ├── openai_large.py          # text-embedding-3-large
│   │   │   └── openai_small.py          # text-embedding-3-small
│   │   └── results/                     # embedding_model_results.json
│   │
│   └── llm-provider/                     # [Phase 3.5 🆕]
│       ├── evaluate.py                   # Answer quality + weighted scorecard
│       ├── base.py                       # BaseLLMProvider ABC
│       ├── config.py                     # API keys, chunk settings, paths
│       ├── requirements.txt
│       ├── providers/
│       │   ├── openrouter.py            # 6 multi-model routing via OpenRouter
│       │   ├── openai_direct.py         # gpt-4o, gpt-4o-mini
│       │   ├── anthropic_direct.py      # claude-3.5-sonnet, claude-3-haiku
│       │   └── ollama.py                # Self-hosted llama3.1:8b
│       └── results/                     # llm_provider_results.json
│
├── tests/                                # [Phase 5 🆕] Integration testing
│   ├── integration/
│   │   ├── conftest.py                  # Pytest fixtures (TestClient, auth tokens)
│   │   └── test_scenarios.py            # 27 E2E tests across 7 scenarios
│   ├── load/
│   │   └── locustfile.py                # Locust load test (EmployeeUser + CustomerUser)
│   └── requirements.txt                 # pytest, locust, httpx, pytest-asyncio
│
├── api/                                  # [Phase 4 🆕] FastAPI application
│   ├── main.py                          # FastAPI app, route registration
│   ├── config.py                        # Pydantic settings from .env
│   ├── store.py                         # In-memory PoC: users, passwords, documents
│   ├── auth/
│   │   ├── models.py                   # User, UserType, Permission, AccessLevel, RBAC
│   │   ├── jwt_handler.py              # Token encode/decode, password hashing
│   │   └── dependencies.py             # FastAPI dependency injection (auth, permissions)
│   ├── rag/
│   │   ├── models.py                   # Pydantic schemas: ChatRequest, ChatResponse
│   │   ├── retrieval.py                # Permission-filtered vector search
│   │   └── pipeline.py                 # run_rag() orchestrator
│   └── routes/
│       ├── auth_routes.py              # POST /api/v1/auth/token
│       ├── chat.py                     # POST /api/v1/chat/completions
│       ├── documents.py                # GET/POST /api/v1/documents/*
│       └── webhooks/
│           └── line.py                 # POST /api/v1/webhooks/line (LINE Messaging API)
│
├── docs/
│   ├── README.md                          # Docs hub (Thai)
│   ├── glossary.md                        # RAG terminology glossary (Thai)
│   ├── phases/                            # Per-phase detailed docs (7 files)
│   ├── guides/
│   │   ├── quickstart.md                  # Setup + all phases
│   │   ├── api-usage.md                   # API Server usage (Phase 4)
│   │   ├── benchmarking.md                # Benchmark guide + interpreting results
│   │   └── adding-adapters.md             # How to add new adapters
│   ├── adr/                               # 6 Architecture Decision Records
│   ├── rfc/RFC-001-rag-tech-stack.md      # RFC draft (TODO sections pending benchmarks)
│   ├── presentation/outline.md            # Presentation outline
│   └── CODEMAPS/                          # You are here
│
├── README.md                              # Project README (Thai)
├── CONTRIBUTING.md                        # Contribution guide
└── CLAUDE.md                              # Claude Code guidance
```

---

## Phase Status

| Phase | Name | Status | Key Output |
|-------|------|--------|-----------|
| 1 | Vector DB Comparison | ✅ Code done | `run_benchmark.py` + 4 adapters |
| 2 | RAG Framework Comparison | 🔄 Code done, not run yet | `evaluate.py` + 4 framework PoCs |
| 3 | Embedding Model Comparison | 🔄 Code done | `evaluate.py` + 5 model adapters (Thai/Eng) |
| 3.5 | LLM Provider Comparison | 🆕 Code done | `evaluate.py` + 4 provider adapters (11 models) |
| 4 | API Layer & Auth Design | 🆕 Code done | FastAPI + JWT + RBAC + Permission-Filtered Retrieval + LINE webhook |
| 5 | Integration Testing | 🆕 Code done | 27 E2E tests, 7 scenarios, Locust load testing |
| 6 | RFC & Knowledge Sharing | 🔄 Docs done | RFC draft, 6 ADRs, guides, glossary, presentation outline |

---

## Common Commands

All commands now use `uv` for reproducible installs:

```bash
# Phase 1 — Vector DB benchmarks
uv sync --group bench-vectordb
make up-db && make benchmark-quick

# Phase 2 — RAG frameworks (needs OPENROUTER_API_KEY)
uv sync --group bench-rag
make rag-eval

# Phase 2 — indexing only (no API key needed)
make rag-eval-no-llm

# Single framework
make rag-eval-framework F=bare_metal

# Phase 3 — embedding models (open-source, no API key)
uv sync --group bench-embed
make embed-eval

# Phase 3 — with OpenAI models
make embed-eval-all

# Single model
make embed-eval-model M=bge_m3

# Phase 3.5 — LLM providers
uv sync --group bench-llm
make llm-eval                   # OpenRouter only
make llm-eval-all               # All providers
make llm-eval-provider P=openai # Single provider

# Phase 4 — FastAPI server
uv sync --group api
make api-run                    # http://localhost:8000/docs

# Phase 5 — Integration testing
uv sync --group test
make test-integration           # 27 E2E tests
make load-test U=100 T=60s      # Load test: 100 users, 60s

# All phases at once
uv sync --all-groups
```

### Phase 4 Example Flows

**Login via JWT:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bob_employee&password=emp123"
# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

**Query RAG with permission-filtered retrieval:**
```bash
TOKEN="eyJ..."
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is the leave policy?"}], "top_k": 3}'
# Response: {"answer": "...", "retrieved_chunks": [...], "model": "anthropic/claude-3-haiku"}
```

**Get current user info + permissions:**
```bash
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
# Response: {"user_id": "u002", "username": "bob_employee", "user_type": "employee", "permissions": [...]}
```

---

## Key Design Principle

Both benchmarks use **Port & Adapter pattern**:
- Abstract base class defines the interface
- Concrete implementations are swappable
- Orchestrator never touches DB/framework-specific code

This ensures the final architecture recommendation is based on evidence, not vendor preference.
