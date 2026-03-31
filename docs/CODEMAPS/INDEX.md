<!-- Generated: 2026-03-31 | Files scanned: 52 | Token estimate: ~480 -->

# RAG Spike Codemaps Index

**Last Updated:** 2026-03-31 | **Project Phase:** 1 ✅ Vector DB | 2 🔄 RAG Framework | 3 🔄 Embedding Models | 3.5 🆕 LLM Providers | 4 🆕 API Layer | 5 🆕 Integration Testing

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
├── Makefile                                 # make benchmark-*, make rag-eval*
├── .env.example                             # Environment variables template
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
└── docs/CODEMAPS/                        # You are here
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
| 6 | RFC + Knowledge Sharing | ⏳ Not started | Final RFC document |

---

## Common Commands

```bash
# Phase 1
make install && make up-db && make benchmark-quick

# Phase 2 (needs OPENROUTER_API_KEY in .env)
make install-rag && make rag-eval

# Phase 2 (no API key — indexing only)
make install-rag && make rag-eval-no-llm

# Single framework
make rag-eval-framework F=bare_metal

# Phase 3 (open-source models, no API key)
make install-embed && make embed-eval

# Phase 3 (all models including OpenAI)
make install-embed && make embed-eval-all

# Single embedding model
make embed-eval-model M=bge_m3

# Phase 3.5 (OpenRouter only, needs OPENROUTER_API_KEY in .env)
make install-llm && make llm-eval

# Phase 3.5 (all 11 providers, needs all API keys)
make install-llm && make llm-eval-all

# Single LLM provider
make llm-eval-provider P=openrouter_gpt4o_mini

# Phase 4 (FastAPI API server)
make api-run                               # Run on http://localhost:8000

# Phase 4 (View API docs)
# Visit: http://localhost:8000/docs (Swagger UI)
#        http://localhost:8000/redoc (ReDoc)

# Phase 5 (Integration testing)
make install-test
make test-integration              # 27 E2E tests, 7 scenarios

# Phase 5 (Load testing — with running api-run)
make load-test                     # Locust headless: 50 users, 30s
locust -f tests/load/locustfile.py # Interactive UI at http://localhost:8089
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
