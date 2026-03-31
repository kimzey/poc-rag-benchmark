<!-- Generated: 2026-03-31 | Files scanned: 22 | Token estimate: ~850 -->

# Dependencies & Infrastructure Codemap

**Last Updated:** 2026-03-31 | **Package Manager:** uv (unified Python dependency management)

---

## Python Package Manager — uv

**File:** `pyproject.toml` (single source of truth)
**Lock file:** `uv.lock` (reproducible installs)

All Python installs are now managed via `uv sync --group <name>`:

```bash
# Install dependencies for specific phase
uv sync --group bench-vectordb   # Phase 1
uv sync --group bench-rag        # Phase 2 (heavy: torch + 3 frameworks)
uv sync --group bench-embed      # Phase 3 (torch + sentence-transformers)
uv sync --group bench-llm        # Phase 3.5 (LLM provider clients)
uv sync --group api              # Phase 4 (FastAPI + JWT + RBAC)
uv sync --group test             # Phase 5 (pytest + locust + api deps)
uv sync --all-groups             # All phases at once
```

Benefits: single lock file, no per-benchmark requirements.txt, reproducible environments.

---

## Phase 1 — Vector DB Benchmarks

**Group:** `bench-vectordb` in `pyproject.toml`

| Package | Version | Purpose |
|---------|---------|---------|
| `qdrant-client` | ≥1.9.0 | Qdrant SDK |
| `psycopg2-binary` | ≥2.9.9 | PostgreSQL + pgvector |
| `pgvector` | ≥0.2.5 | PG vector type |
| `pymilvus` | ≥2.4.0 | Milvus gRPC |
| `opensearch-py` | ≥2.5.0 | OpenSearch HTTP |
| `numpy` | ≥1.26.0 | Vector math |
| `rich` | ≥13.7.0 | Terminal output |
| `tqdm` | ≥4.66.0 | Progress bars |
| `python-dotenv` | ≥1.0.0 | `.env` loading |

**Install:** `uv sync --group bench-vectordb`

---

## Phase 2 — RAG Framework Benchmarks

**Group:** `bench-rag` in `pyproject.toml` (~2GB total)

### Core
| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | ≥1.30.0 | OpenRouter (OpenAI-compatible) |
| `sentence-transformers` | ≥3.0.0 | Local embeddings |
| `torch` | ≥2.0.0 | Backend |
| `python-dotenv` | ≥1.0.0 | `.env` loading |
| `rich` | ≥13.7.0 | Comparison tables |
| `numpy` | ≥1.26.0 | Cosine similarity |

### Frameworks
| Package | Version | Framework | Purpose |
|---------|---------|-----------|---------|
| `llama-index-core` | ≥0.11 | LlamaIndex | Core abstractions |
| `llama-index-llms-openai` | ≥0.3 | LlamaIndex | OpenRouter adapter |
| `llama-index-embeddings-huggingface` | ≥0.3 | LlamaIndex | HF models bridge |
| `langchain` | ≥0.3 | LangChain | Chain primitives |
| `langchain-community` | ≥0.3 | LangChain | FAISS, loaders |
| `langchain-openai` | ≥0.2 | LangChain | OpenRouter adapter |
| `langchain-huggingface` | ≥0.1 | LangChain | HF embeddings |
| `faiss-cpu` | ≥1.8.0 | LangChain | Vector store |
| `haystack-ai` | ≥2.5.0 | Haystack | Full v2 stack |

**Install:** `uv sync --group bench-rag`

**External service:** OpenRouter (`OPENROUTER_API_KEY` in `.env`)

## Phase 3 — Embedding Model Benchmarks

**Group:** `bench-embed` in `pyproject.toml`

| Package | Version | Purpose |
|---------|---------|---------|
| `sentence-transformers` | ≥3.0.0 | Open-source models (HuggingFace) |
| `torch` | ≥2.0.0 | Backend |
| `openai` | ≥1.30.0 | OpenAI embedding API (optional) |
| `python-dotenv` | ≥1.0.0 | `.env` loading |
| `numpy` | ≥1.26.0 | Cosine similarity |
| `rich` | ≥13.7.0 | Scorecards |

**Models:** BAAI/bge-m3, intfloat/multilingual-e5-large, mixedbread-ai/mxbai-embed-large-v1 (open-source)
**Optional:** text-embedding-3 models via `OPENAI_API_KEY`

**Install:** `uv sync --group bench-embed`

---

## Phase 3.5 — LLM Provider Benchmarks

**Group:** `bench-llm` in `pyproject.toml`

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | ≥1.30.0 | OpenAI + OpenRouter + Ollama (OpenAI-compatible) |
| `anthropic` | ≥0.28.0 | Anthropic Direct API |
| `python-dotenv` | ≥1.0.0 | `.env` loading |
| `rich` | ≥13.7.0 | Scorecards |

**Providers:** OpenRouter (multi-model), OpenAI Direct, Anthropic Direct, Ollama (self-hosted)

**Install:** `uv sync --group bench-llm`

**External services:**
- OpenRouter: `OPENROUTER_API_KEY`
- OpenAI: `OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- Ollama: Local at `http://localhost:11434`


## Docker Infrastructure

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

## Phase 4 — API Server

**Group:** `api` in `pyproject.toml`

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ==0.115.12 | Web framework, routes, dependency injection |
| `uvicorn[standard]` | ==0.34.0 | ASGI server, auto-reload |
| `pydantic` | ==2.11.3 | Request/response schemas |
| `pydantic-settings` | ==2.8.1 | `.env` config loading |
| `python-jose[cryptography]` | ==3.3.0 | JWT encode/decode |
| `passlib[bcrypt]` | ==1.7.4 | Password hashing |
| `bcrypt` | ==4.0.1 | HMAC backend |
| `openai` | ==1.71.0 | LLM endpoint client |
| `httpx` | ==0.28.1 | Async HTTP (LINE webhooks) |
| `python-multipart` | ==0.0.20 | Form data parsing |

**Install:** `uv sync --group api`

**Run:** `uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`

---

## Phase 5 — Integration & Load Testing

**Group:** `test` in `pyproject.toml` (includes `api` group)

| Package | Version | Purpose |
|---------|---------|---------|
| (includes api) | — | All Phase 4 dependencies |
| `pytest` | ==8.3.5 | Test framework + fixtures |
| `pytest-asyncio` | ==0.25.3 | Async test support |
| `locust` | ==2.32.4 | Load testing (concurrent users) |

**Install:** `uv sync --group test`

---

## Makefile Install Targets

All Makefile targets now use `uv sync`:

```bash
make install           # uv sync --group bench-vectordb
make install-rag       # uv sync --group bench-rag
make install-embed     # uv sync --group bench-embed
make install-llm       # uv sync --group bench-llm
make install-api       # uv sync --group api
make install-test      # uv sync --group test
```

Run commands are wrapped in `uv run`:

```bash
make benchmark-quick   # uv run python benchmarks/vector-db/run_benchmark.py --n 10000
make api-run           # uv run uvicorn api.main:app --reload ...
make test-integration  # uv run pytest tests/integration/ -v --tb=short -s
make load-test         # uv run locust -f tests/load/locustfile.py ...
```

---

## Environment Variables

**File:** `.env.example`

**Phase 2-3.5 — LLM & Embedding:**
```bash
OPENROUTER_API_KEY=sk-or-...           # OpenRouter multi-model gateway
OPENAI_API_KEY=sk-...                   # OpenAI API (embedding + direct LLM)
ANTHROPIC_API_KEY=sk-ant-...            # Anthropic Direct (optional)
RAG_LLM_MODEL=openai/gpt-4o-mini
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3
```

**Phase 4-5 — API Server:**
```bash
JWT_SECRET_KEY=dev-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

OPENROUTER_MODEL=openai/gpt-4o-mini
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
```

---

## Hardware Requirements

| Phase | CPU | RAM | Disk | Note |
|-------|-----|-----|------|------|
| Phase 1 | 4+ | 8GB+ | 10GB+ | Milvus + OpenSearch each need 2GB |
| Phase 2 | 2+ | 4GB+ | 1GB+ | sentence-transformers 80–500MB |
| Phase 3 | 2+ | 4GB+ | 2GB+ | Embedding models 500MB–1.5GB |
| Phase 3.5 (Ollama) | 4+ + GPU | 16GB+ | 10GB+ | Local LLM; CPU-only ~5–10s/token |
| Phase 3.5 (API) | 1+ | 2GB+ | 100MB | Network-based |
| Phase 4-5 | 2+ | 4GB+ | 1GB+ | FastAPI + tests |

---

## Quick Install Commands

```bash
# Phase 1: Vector DB benchmarks
uv sync --group bench-vectordb && make up-db && make benchmark-quick

# Phase 2: RAG frameworks (needs OPENROUTER_API_KEY)
uv sync --group bench-rag && make rag-eval

# Phase 3: Embedding models (open-source only)
uv sync --group bench-embed && make embed-eval

# Phase 4: API server
uv sync --group api && make api-run

# Phase 5: Integration tests
uv sync --group test && make test-integration

# All phases at once
uv sync --all-groups
```
