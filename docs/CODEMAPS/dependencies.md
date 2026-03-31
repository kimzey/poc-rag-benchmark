<!-- Generated: 2026-03-31 | Files scanned: 22 | Token estimate: ~1050 -->

# Dependencies & Infrastructure Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 ✅ + 2 🔄 + 3 🔄 + 3.5 🆕 + 4 🆕 + 5 🆕 (Integration Testing)

---

## Phase 1 — Python Packages

**File:** `benchmarks/vector-db/requirements.txt`

| Package | Version | Purpose | Adapter |
|---------|---------|---------|---------|
| `qdrant-client` | ≥1.9.0 | Qdrant SDK | QdrantAdapter |
| `psycopg2-binary` | ≥2.9.9 | PostgreSQL | PgvectorAdapter |
| `pgvector` | ≥0.2.5 | PG vector type | PgvectorAdapter |
| `pymilvus` | ≥2.4.0 | Milvus gRPC | MilvusAdapter |
| `opensearch-py` | ≥2.5.0 | OpenSearch HTTP | OpenSearchAdapter |
| `numpy` | ≥1.26.0 | Vector math, ground truth | dataset.py |
| `rich` | ≥13.7.0 | Terminal tables | run_benchmark.py |
| `tqdm` | ≥4.66.0 | Progress bars | optional |
| `python-dotenv` | ≥1.0.0 | Env config | optional |

---

## Phase 2 — Python Packages

**File:** `benchmarks/rag-framework/requirements.txt`

### Core
| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | ≥1.30.0 | OpenRouter client (OpenAI-compatible) |
| `sentence-transformers` | ≥3.0.0 | Local embeddings (no API key) |
| `torch` | ≥2.0.0 | Backend for sentence-transformers |
| `python-dotenv` | ≥1.0.0 | Load `.env` |
| `rich` | ≥13.7.0 | Comparison tables |
| `numpy` | ≥1.26.0 | Cosine similarity (bare_metal) |

### RAG Frameworks
| Package | Framework | Purpose |
|---------|-----------|---------|
| `llama-index-core` ≥0.11 | LlamaIndex | Core: VectorStoreIndex, SimpleDirectoryReader |
| `llama-index-llms-openai` ≥0.3 | LlamaIndex | OpenRouter via OpenAI-compat LLM |
| `llama-index-embeddings-huggingface` ≥0.3 | LlamaIndex | sentence-transformers bridge |
| `langchain` ≥0.3 | LangChain | Core chain primitives |
| `langchain-community` ≥0.3 | LangChain | FAISS, TextLoader |
| `langchain-openai` ≥0.2 | LangChain | ChatOpenAI → OpenRouter |
| `langchain-huggingface` ≥0.1 | LangChain | HuggingFaceEmbeddings |
| `faiss-cpu` ≥1.8.0 | LangChain | In-memory vector store |
| `haystack-ai` ≥2.5.0 | Haystack | Full Haystack v2 (InMemory + pipelines) |

---

## Phase 2 — External Services

| Service | Auth | Used By | Notes |
|---------|------|---------|-------|
| **OpenRouter** | `OPENROUTER_API_KEY` | All 4 frameworks | OpenAI-compatible, `base_url=https://openrouter.ai/api/v1` |
| sentence-transformers model | None | All 4 frameworks | Downloaded from HuggingFace Hub on first run, cached locally |

Default model: `anthropic/claude-3-haiku` (fast + cheap for spike)

## Phase 3.5 — External Services

| Service | Auth | Used By | Notes |
|---------|------|---------|-------|
| **OpenRouter** | `OPENROUTER_API_KEY` | Phase 3.5 provider adapter | Multi-model gateway, 6+ LLMs available |
| **OpenAI Direct** | `OPENAI_API_KEY` | Phase 3.5 provider adapter | gpt-4o, gpt-4o-mini endpoints |
| **Anthropic Direct** | `ANTHROPIC_API_KEY` | Phase 3.5 provider adapter | claude-3.5-sonnet, claude-3-haiku |
| **Ollama** | None (local) | Phase 3.5 provider adapter | Self-hosted at `http://localhost:11434` (default) |

Default provider: `openrouter_gpt4o_mini` (multi-model routing, cost-effective)

---

## Phase 3 — Python Packages

**File:** `benchmarks/embedding-model/requirements.txt`

| Package | Purpose |
|---------|---------|
| `sentence-transformers` ≥3.0.0 | Open-source embedding models (HF hub) |
| `numpy` ≥1.26.0 | Normalization, cosine retrieval |
| `torch` ≥2.0.0 | Backend for sentence-transformers |
| `openai` ≥1.30.0 | OpenAI text-embedding-3 models (optional) |
| `rich` ≥13.7.0 | Comparison tables + scorecard |
| `python-dotenv` ≥1.0.0 | Load `.env` for OPENAI_API_KEY |

**Open-source models (no API key):** BAAI/bge-m3, intfloat/multilingual-e5-large, mixedbread-ai/mxbai-embed-large-v1

**API models (optional):** text-embedding-3-large, text-embedding-3-small (requires `OPENAI_API_KEY`)

---

## Phase 3.5 — Python Packages

**File:** `benchmarks/llm-provider/requirements.txt`

| Package | Purpose |
|---------|---------|
| `openai` ≥1.30.0 | OpenAI & OpenRouter & Ollama (all OpenAI-compatible) |
| `anthropic` ≥0.40.0 | Anthropic Direct client (if using Anthropic provider) |
| `rich` ≥13.7.0 | Comparison tables + scorecard |
| `python-dotenv` ≥1.0.0 | Load `.env` for API keys |

---

## Phase 1 — Docker Infrastructure

**File:** `docker/docker-compose.vector-db.yml`

| Service | Image | Ports | Depends On |
|---------|-------|-------|-----------|
| `qdrant` | qdrant/qdrant:v1.9.2 | 6333 (REST), 6334 (gRPC) | — |
| `pgvector` | pgvector/pgvector:pg16 | 5433→5432 | — |
| `milvus` | milvusdb/milvus:v2.4.5 | 19530 (gRPC), 9091 | etcd, minio |
| `opensearch` | opensearchproject/opensearch:2.13.0 | 9200, 9600 | — |
| `etcd` | quay.io/coreos/etcd:v3.5.5 | internal | — |
| `minio` | minio/minio:2023-03-20 | 9000, 9001 | — |

**Volumes:** `qdrant_data`, `pgvector_data`, `etcd_data`, `minio_data`, `milvus_data`, `opensearch_data`

---

## Makefile Targets

### Phase 1
```bash
make install            # pip install benchmarks/vector-db/requirements.txt
make up-db              # docker compose up -d (all DBs)
make up-db DB=qdrant    # single DB
make down-db            # docker compose down -v
make benchmark-quick    # 10K vectors
make benchmark-medium   # 100K vectors
make benchmark-all      # both
make benchmark-db DB=qdrant N=50000
```

### Phase 2
```bash
make install-rag                       # pip install rag-framework/requirements.txt
make rag-eval                          # all 4 frameworks (needs OPENROUTER_API_KEY)
make rag-eval-no-llm                   # indexing only, no API key needed
make rag-eval-framework F=bare_metal   # single framework
```

### Phase 3
```bash
make install-embed                     # pip install embedding-model/requirements.txt
make embed-eval                        # all open-source models (no API key)
make embed-eval-all                    # all models (requires OPENAI_API_KEY for OpenAI)
make embed-eval-model M=bge_m3        # single model
make embed-eval-topk K=5               # override top-k (default: 3)
```

### Phase 3.5
```bash
make install-llm                       # pip install llm-provider/requirements.txt
make llm-eval                          # OpenRouter only (needs OPENROUTER_API_KEY)
make llm-eval-all                      # all 11 providers (needs all API keys)
make llm-eval-provider P=openrouter_gpt4o_mini  # single provider
make llm-eval-topk K=5                 # override top-k (default: 3)
```

---

## Environment Variables

**File:** `.env.example`

```bash
# Phase 2 (LLM)
OPENROUTER_API_KEY=sk-or-...
RAG_LLM_MODEL=anthropic/claude-3-haiku

# Phase 2 (Embeddings — local, no key needed)
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2    # fast; use multilingual-e5-small for Thai

# Phase 2 & 3 & 3.5 (Tuning — same chunk config for comparison fairness)
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3

# Phase 3 (Optional — for OpenAI embedding models)
OPENAI_API_KEY=sk-...                   # Required only for text-embedding-3-* models

# Phase 3.5 (LLM Providers)
OPENROUTER_API_KEY=sk-or-...            # OpenRouter multi-model gateway
OPENAI_API_KEY=sk-...                   # OpenAI Direct (gpt-4o, gpt-4o-mini)
ANTHROPIC_API_KEY=sk-ant-...            # Anthropic Direct (claude-3.5-sonnet)
OLLAMA_BASE_URL=http://localhost:11434  # Ollama self-hosted LLM
OLLAMA_MODEL=llama3.1:8b                # Ollama model to use

# Phase 3.5 (Generation tuning)
LLM_MAX_NEW_TOKENS=512                  # Max tokens for answer generation
LLM_TEMPERATURE=0.0                     # Temperature for consistency
```

---

## Hardware Requirements

| Phase | CPU | RAM | Disk | Note |
|-------|-----|-----|------|------|
| Phase 1 | 4+ cores | 8GB+ | 10GB+ | Milvus + OpenSearch need ≥2GB each |
| Phase 2 | 2+ cores | 4GB+ | 1GB+ | sentence-transformers model ~80–500MB |
| Phase 3 | 2+ cores | 4GB+ | 2GB+ | Embedding models (BGE-M3, E5-large) ~500MB–1.5GB |
| Phase 3.5 (Ollama) | 4+ cores + GPU | 16GB+ | 10GB+ | Local LLM inference; CPU-only slower (~5–10s/token) |
| Phase 3.5 (API) | 1+ core | 2GB+ | 100MB | Network-based; no local compute needed

---

## Phase 4 — Python Packages

**File:** `api/requirements.txt` (expected)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.100.0 | Web framework, async routes, dependency injection |
| `uvicorn` | ≥0.23.0 | ASGI server, hot reload |
| `pydantic` | ≥2.0.0 | Request/response validation, User/Chat models |
| `pydantic-settings` | ≥2.0.0 | `.env` configuration loading |
| `python-jose` | ≥3.3.0 | JWT token encode/decode (HMAC-SHA256) |
| `passlib` | ≥1.7.0 | Password hashing (bcrypt) |
| `httpx` | ≥0.24.0 | Async HTTP client for LINE webhook replies |
| `openai` | ≥1.30.0 | OpenAI-compatible LLM endpoint (OpenRouter/Anthropic/OpenAI) |
| `python-dotenv` | ≥1.0.0 | `.env` loading |

---

## Phase 4 — Environment Variables

**File:** `.env.example` (Phase 4 additions)

```bash
# Phase 4: FastAPI app
OPENAPI_URL=/docs
REDOC_URL=/redoc
APP_NAME="RAG API — Phase 4 PoC"

# Phase 4: JWT
JWT_SECRET_KEY=your-secret-key-here            # Used for signing tokens
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Phase 4: LLM (same as Phase 3.5)
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
RAG_LLM_MODEL=anthropic/claude-3-haiku         # Default: fast + cheap

# Phase 4: LINE Webhook
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token

# Phase 4: Retrieval tuning
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3
```

---

## Phase 4 — Makefile Targets

```bash
make api-run          # uvicorn api.main:app --reload
make api-docs         # Visit http://localhost:8000/docs
make api-test         # pytest tests/api/
```

---

## Phase 4 — Infrastructure Notes

**PoC Stores (api/store.py):**
- user_store: Dict[user_id, User] — 5 demo users with roles
- password_store: Dict[username, hashed_pwd] — PoC credentials
- doc_store: List[Document] — 5 sample documents with access levels

**Production Replacements:**
| Component | PoC | Production |
|-----------|-----|-----------|
| user_store | In-memory dict | PostgreSQL users table + sessions |
| doc_store | In-memory list | Vector DB (Qdrant/Milvus) with metadata filters |
| doc embedding | Placeholder | Real embeddings (BGE-M3 or text-embedding-3) |
| LLM endpoint | Mock or OpenRouter | OpenRouter / Direct API / Self-hosted Ollama |

**API Server:**
- Dev: `uvicorn api.main:app --reload` on http://localhost:8000
- Prod: `uvicorn api.main:app --host 0.0.0.0 --port 8000` or Docker
- OpenAPI schema at `/docs` (Swagger UI) and `/redoc` (ReDoc)

**Authentication Flow:**
1. User calls `POST /api/v1/auth/token` with username + password
2. Server looks up password_store, verifies hash
3. Creates JWT token with user_id, username, user_type
4. Client sends token in `Authorization: Bearer <token>` header
5. Subsequent requests use FastAPI Depends(get_current_user) to extract user
6. Route-level checks enforce permissions: `Depends(require_permission(Permission.chat_query))`

**Permission-Filtered Retrieval:**
- VectorDB filter (production): metadata filter on insert (Qdrant `query_filter`)
- PoC simulation: Python list comprehension filtering visible docs before scoring
- Both enforce: access_level visibility BEFORE similarity scoring (secure-by-design)

---

## Phase 5 — Python Packages

**File:** `tests/requirements.txt`

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥8.3.0 | Test framework + fixtures |
| `pytest-asyncio` | ≥0.25.0 | Async test support (for async endpoints) |
| `httpx` | ≥0.28.0 | Async HTTP client (for TestClient) |
| `locust` | ≥2.32.0 | Load testing framework (concurrent users) |

**Installed via:** `make install-test` (installs both Phase 4 API + Phase 5 test deps)

---

## Phase 5 — Makefile Targets

```bash
make install-test                      # pip install api + tests/requirements.txt
make test-integration                  # pytest tests/integration/ -v --tb=short
make test-integration-verbose          # pytest tests/integration/ -v --tb=long (no capture)
make load-test                         # Locust headless: 50 users, 30s (requires api-run)
make load-test U=100 R=10 T=60s       # Override users, spawn rate, run-time
```

---

## Phase 5 — Test Coverage

**7 End-to-End Scenarios (27 tests):**

| Scenario | Tests | Coverage |
|----------|-------|----------|
| 1. Employee uploads & queries | 2 | Document upload, search indexing |
| 2. Customer access control | 2 | Permission-based doc visibility |
| 3. LINE webhook → chat | 3 | Signature validation, message reply |
| 4. Concurrent load | 5 | Rate limiting, response consistency |
| 5. Component swap (LLM) | 4 | Mock vs real provider, fallbacks |
| 6. Error handling | 4 | Timeout (503), connection errors, malformed input |
| 7. Thai language E2E | 3 | Thai query → retrieval → answer |

**Load Test (Locust):**
- EmployeeUser (3x weight): 4 chat queries (En) + 3 chat queries (Th) + 2 doc searches per cycle
- CustomerUser (1x weight): 2 chat queries (Customer FAQ) + 2 faq-search per cycle
- Default: 50 users, spawn-rate 5/s, run 30s
- Metrics: p50/p95/p99 latency, throughput, error rate
