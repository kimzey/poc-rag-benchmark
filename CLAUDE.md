# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG tech stack spike — evaluates Vector DBs, RAG frameworks, embedding models, LLM providers, API auth patterns, and integration testing. This is a PoC/benchmarking project, not a production service. Written in Thai+English.

## Commands

```bash
# Setup
make setup                   # Check prerequisites, create .env

# Install deps (per-phase groups via uv)
make install                 # Phase 1: vector-db benchmarks
make install-rag             # Phase 2: RAG frameworks (~2GB)
make install-embed           # Phase 3: embedding models
make install-llm             # Phase 3.5: LLM providers
make install-api             # Phase 4: FastAPI server
make install-test            # Phase 5: integration tests (includes api)

# Run API server
make api-run                 # http://localhost:8000/docs

# Tests
make test-integration        # All 27 integration tests (no running server needed)
uv run pytest tests/integration/ -v -k "TestScenario1"  # Single scenario

# Benchmarks
make benchmark-quick         # 10K vectors (requires Docker: make up-db)
make rag-eval                # All 4 RAG frameworks (requires OPENROUTER_API_KEY)
make embed-eval              # Open-source embedding models
make llm-eval                # Default LLM provider
```

## Architecture

**6-phase spike structure** — each phase builds on the previous, with independent benchmarking directories:

- `benchmarks/vector-db/` — Phase 1: Qdrant, pgvector, Milvus, OpenSearch comparison. Each client implements `VectorDBClient` ABC (`clients/base.py`). Docker services in `docker/docker-compose.vector-db.yml`.
- `benchmarks/rag-framework/` — Phase 2: bare_metal, LlamaIndex, LangChain, Haystack. Each implements `BaseRAGPipeline` ABC (`base.py`). Evaluate via `evaluate.py`.
- `benchmarks/embedding-model/` — Phase 3: BGE-M3, multilingual-E5, MxBai, OpenAI. Each implements `BaseEmbeddingModel` ABC (`base.py`).
- `benchmarks/llm-provider/` — Phase 3.5: OpenRouter, OpenAI direct, Anthropic, Ollama. Each implements `BaseLLMProvider` ABC (`base.py`).
- `api/` — Phase 4: FastAPI server with JWT auth + RBAC + permission-filtered retrieval.
- `tests/` — Phase 5: Integration tests (pytest + FastAPI TestClient) and load tests (Locust).

**API layer (`api/`):**
- Entry point: `api/main.py` → FastAPI app, all routes under `/api/v1`
- Auth: `api/auth/` — JWT tokens, 4 user types (admin/employee/customer/service), RBAC via `Permission` enum, document access via `AccessLevel` enum
- RAG pipeline: `api/rag/pipeline.py` wires retrieve → prompt → LLM. Falls back to mock if no API key. Retrieval in `api/rag/retrieval.py` is a simulated vector search (replace `_vector_search()` for real DB).
- `api/store.py` — in-memory document store (PoC only)
- `api/routes/webhooks/line.py` — LINE Messaging API adapter

**Key design patterns:**
- Each benchmark category uses an ABC base class with uniform interface → implementations are pluggable
- Permission filtering happens at retrieval level via `access_level` metadata, not post-hoc
- `uv` for env management — deps are split into groups per phase in `pyproject.toml`. `uv sync --group <name>` switches the venv to match that group
- Test datasets in `datasets/` (Thai HR policy, English tech docs, mixed FAQ, question set)

## Environment

- Python ≥ 3.11, managed by `uv` (not pip/poetry)
- All commands use `uv run` — no need to activate venv manually
- `.env` for API keys (copy from `.env.example`). API server works without keys (mock LLM mode)
- Test users: alice_admin/admin123, bob_employee/emp123, carol_customer/cust123, svc_line_bot/svc123
