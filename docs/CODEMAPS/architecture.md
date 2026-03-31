<!-- Generated: 2026-03-31 | Files scanned: 62 | Token estimate: ~1350 -->

# Architecture Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 ✅ + 2 🔄 + 3 🔄 + 3.5 🆕 + 4 🆕 (API Layer) + 5 🆕 (Integration Tests)

## Overview

RAG spike เป็น research project แบบ multi-phase เพื่อ evaluate tech stack สำหรับ RAG system ใน production โดยใช้ **Port & Adapter pattern** ทั้งสองเฟสเพื่อป้องกัน vendor lock-in

## System Diagram

```
spike-rak/
│
├── [Phase 1 ✅] Vector DB Benchmark ──────────────────────────────
│   benchmarks/vector-db/run_benchmark.py
│     └─ VectorDBClient (ABC, 6 methods)
│         ├─ QdrantAdapter       → localhost:6333
│         ├─ PgvectorAdapter     → localhost:5433
│         ├─ MilvusAdapter       → localhost:19530
│         └─ OpenSearchAdapter   → localhost:9200
│   Data: synthetic 10K–100K unit-norm vectors (dim=1536)
│   Metrics: p50/p95/p99 latency, QPS, recall@10
│
├── [Phase 2 🔄] RAG Framework Comparison ─────────────────────────
│   benchmarks/rag-framework/evaluate.py
│     └─ BaseRAGPipeline (ABC)
│         ├─ BareMetalRAGPipeline   (numpy cosine + direct OpenRouter)
│         ├─ LlamaIndexRAGPipeline  (VectorStoreIndex, global Settings)
│         ├─ LangChainRAGPipeline   (FAISS, RetrievalQA chain)
│         └─ HaystackRAGPipeline    (DAG pipeline, InMemoryDocumentStore)
│   Data: Thai + English + Mixed documents (3 docs, 10 questions)
│   LLM: OpenRouter (configurable model)
│   Embeddings: sentence-transformers (local, no API key)
│
├── [Phase 3 🔄] Embedding Model Comparison ─────────────────────
│   benchmarks/embedding-model/evaluate.py
│     └─ BaseEmbeddingModel (ABC)
│         ├─ BGEM3Model            (BAAI/bge-m3, multilingual)
│         ├─ MultilingualE5LargeModel  (intfloat/multilingual-e5-large, query/passage prefix)
│         ├─ MxbaiEmbedLargeModel      (mixedbread-ai/mxbai-embed-large-v1)
│         ├─ OpenAILargeModel      (text-embedding-3-large)
│         └─ OpenAISmallModel      (text-embedding-3-small)
│   Data: Same 3 Thai/English/mixed docs from Phase 2 (reused corpus)
│   Metrics: Recall@k, MRR, latency, cost, self-hostability, weighted scorecard
│
├── [Phase 3.5 🆕] LLM Provider Comparison ─────────────────────
│   benchmarks/llm-provider/evaluate.py
│     └─ BaseLLMProvider (ABC)
│         ├─ OpenRouterProvider      (6 models: gpt-4o, claude-3.5, gemini, llama, deepseek)
│         ├─ OpenAIDirectProvider    (gpt-4o, gpt-4o-mini)
│         ├─ AnthropicDirectProvider (claude-3.5-sonnet, claude-3-haiku)
│         └─ OllamaProvider          (self-hosted llama3.1:8b default)
│   Data: Same 3 docs (TF-IDF retrieval, no embedding model needed)
│   Metrics: Answer quality (F1), latency, cost, lock-in, self-hostability, weighted scorecard
│
└── [Phase 4 🆕] RAG API Layer ───────────────────────────────────────
    api/main.py (FastAPI application)
      Routes:
        POST   /api/v1/auth/token           → JWT login (UserStore)
        POST   /api/v1/chat/completions     → Permission-filtered RAG query
        POST   /api/v1/documents/upload     → Store document in memory
        GET    /api/v1/documents/search     → Search visible documents
        POST   /api/v1/documents/index      → Trigger indexing
        GET    /api/v1/documents/collections → List collections
        GET    /api/v1/me                   → Current user info + permissions
        POST   /api/v1/webhooks/line        → LINE Messaging API adapter
    
    Auth Layer (api/auth/):
      ├─ models.py                    — User, UserType, Permission, AccessLevel
      │                                 RBAC: role → permission set
      │                                 Access matrix: role → visible access levels
      ├─ jwt_handler.py               — Token encode/decode, password hashing
      └─ dependencies.py              — FastAPI Depends() for auth + permissions
    
    RAG Pipeline (api/rag/):
      ├─ models.py                    — Pydantic schemas (ChatRequest, ChatResponse, etc.)
      ├─ retrieval.py                 — Permission-filtered vector search
      │                                 _vector_search() simulates VectorDB with metadata filter
      └─ pipeline.py                  — run_rag(): orchestrates retrieval + LLM call
    
    Document Store (api/store.py):
      ├─ user_store                   — Dict[user_id, User] (5 PoC users)
      ├─ password_store               — Dict[username, hashed_pwd] (PoC credentials)
      └─ doc_store                    — List[Document] (5 sample docs with access_level)
    
    Channel Adapters:
      └─ routes/webhooks/line.py      — LINE Messaging API signature validation + reply
    
    Design:
      • Channel adapter pattern: LINE/Discord/Web → same ChatRequest/ChatResponse
      • RBAC enforced at route level (Depends) and retrieval level (filter)
      • Mock PoC store: replaces with PostgreSQL + Vector DB in production
      • OpenAI-compatible LLM endpoint (OpenRouter/Anthropic/OpenAI direct)
      • Error handling: LLM timeout/connection → 503 Service Unavailable

└── [Phase 5 🆕] Integration Testing ──────────────────────────────────
    tests/integration/conftest.py (pytest fixtures)
      ├─ @fixture client: FastAPI TestClient (in-process, no server needed)
      ├─ @fixture employee_token: JWT for bob_employee
      ├─ @fixture customer_token: JWT for carol_customer
      ├─ @fixture admin_token: JWT for alice_admin
      └─ @fixture clean_doc_store: cleanup after doc uploads
    
    tests/integration/test_scenarios.py (27 E2E tests, 7 scenarios)
      1. Employee uploads document & queries it (2 tests)
      2. Customer queries — sees only allowed docs (2 tests)
      3. LINE user sends question & gets answer (3 tests)
      4. Concurrent queries under load (5 tests)
      5. Component swap test (LLM provider mock vs real) (4 tests)
      6. Error handling — LLM timeout/connection (4 tests)
      7. Thai language end-to-end pipeline (3 tests)
    
    tests/load/locustfile.py (load test)
      ├─ EmployeeUser (3x weight): 4 chat-en + 3 chat-th + 2 doc-search tasks
      └─ CustomerUser (1x weight): 2 chat-customer + 2 faq-search tasks
    
    Target metrics (from plan.md §9.2):
      • p50 latency:       < 3s   (including LLM generation)
      • p95 latency:       < 8s   (including LLM generation)
      • Retrieval p95:     < 200ms (vector search only)
      • Throughput:        > 50 req/sec
```

## Phase 1 — VectorDBClient Interface

**File:** `benchmarks/vector-db/clients/base.py`

```
VectorDBClient (ABC)
├─ connect() → None
├─ create_collection(name) → None
├─ insert(records: list[BenchmarkRecord]) → None
├─ search(vector, top_k, filter?) → list[SearchResult]
├─ count() → int
└─ drop_collection() → None
```

Data flow: `generate_dataset(n)` → `insert()` → `search() × 100` → `LatencyStats`

## Phase 2 — BaseRAGPipeline Interface

**File:** `benchmarks/rag-framework/base.py`

```
BaseRAGPipeline (ABC)
├─ build_index(doc_paths: list[str]) → IndexStats
│   # chunk → embed (sentence-transformers local) → store in-memory
├─ query(question: str, top_k=3) → RAGResult
│   # embed query → cosine retrieve → LLM generate via OpenRouter
└─ loc → int  # non-blank lines in pipeline.py (boilerplate metric)
```

### Framework Implementations

| Framework | Vector Store | Chunker | LLM Setup |
|-----------|-------------|---------|-----------|
| `bare_metal` | numpy dot product | word splitter (custom) | `openai.OpenAI(base_url=openrouter)` |
| `llamaindex` | VectorStoreIndex (RAM) | SentenceSplitter | `LlamaOpenAI(api_base=openrouter)` via global Settings |
| `langchain` | FAISS (RAM) | RecursiveCharacterTextSplitter | `ChatOpenAI(openai_api_base=openrouter)` |
| `haystack` | InMemoryDocumentStore | word splitter (custom) | `OpenAIGenerator(api_base_url=openrouter)` |

### Phase 2 Evaluation Metrics

| Metric | How Measured |
|--------|-------------|
| Indexing time (ms) | `time.perf_counter()` around `build_index()` |
| Query latency (ms) | `time.perf_counter()` around `query()` |
| Non-blank LOC | `pipeline.loc` property counts non-comment lines |
| Component swap-ability | Manual 3-axis assessment (LLM / VectorDB / Embedder) |

## Phase 3 — BaseEmbeddingModel Interface

**File:** `benchmarks/embedding-model/base.py`

```
BaseEmbeddingModel (ABC)
├─ encode(texts: list[str]) → EmbedResult
│   # L2-normalize embeddings, track latency_ms
└─ meta → ModelMeta
   # Static facts: dimensions, max_tokens, cost, vendor_lock_in, self_hostable
```

### Phase 3 Evaluation Metrics

| Metric | How Measured | Higher/Lower |
|--------|-------------|--------------|
| Thai Recall@k | % questions with GT chunk in top-k | Higher |
| Eng Recall@k | % English questions with GT chunk in top-k | Higher |
| MRR | Mean Reciprocal Rank (avg 1/position) | Higher |
| Query Latency (ms) | `time.perf_counter()` for single query encode | Lower |
| Index Latency (ms) | Time to encode all corpus chunks | Lower |
| Cost/1M tokens | USD; 0.0 for open-source | Lower |
| Self-hostable | bool (local download vs API-only) | Higher |
| Vendor Lock-in | 0 (fully open) to 10 (proprietary) | Lower |
| Dimensions | Embedding vector size | Lower (storage) |
| Max Tokens | Context length; input chunk limit | Higher |

**Ground Truth:** Token overlap (Jaccard) of question's expected_answer vs corpus chunks

**Weighted Scorecard:** Thai 25% · Eng 15% · Latency 15% · Cost 15% · Self-host 10% · Dims 5% · MaxTok 5% · Lock-in 10%

## Phase 3.5 — BaseLLMProvider Interface

**File:** `benchmarks/llm-provider/base.py`

```
BaseLLMProvider (ABC)
├─ meta → ProviderMeta
│   # name, model_id, provider, costs, lock-in, self_hostable, openai_compatible
└─ generate(prompt: str, context: str) → GenerateResult
    # wraps _generate_raw(), tracks latency + cost
```

### Phase 3.5 Evaluation Metrics

| Metric | How Measured | Higher/Lower |
|--------|-------------|--------------|
| Overall F1 | Token-overlap F1 of generated vs expected answer | Higher |
| Thai F1 | Avg F1 for Thai-language questions | Higher |
| Avg Latency (ms) | Wall time for one generate() call | Lower |
| Total Cost (USD) | Sum of token costs for all 10 questions | Lower |
| Cost per 1M input tokens | USD pricing for input tokens | Lower |
| Cost per 1M output tokens | USD pricing for output tokens | Lower |
| Vendor Lock-in | 0 (open) to 10 (proprietary) | Lower |
| Self-hostable | bool (local vs API-only) | Higher |
| OpenAI compatible | bool (can swap endpoints) | Higher |
| Reliability | Qualitative: fallback support, uptime SLA | Higher |
| Privacy | Qualitative: where data flows | Higher |
| Ease of switching | Qualitative: cost + effort to switch models | Higher |

**Retrieval:** TF-IDF cosine (no embedding model dependency). For fair comparison, pass `--use-bge` to use BGE-M3.

**Weighted Scorecard:** Quality 20% · Lock-in 20% · Cost 15% · Latency 15% · Thai 10% · Reliability 10% · Privacy 5% · Ease-of-switching 5%

## Entry Points

| File | Phase | Responsibility |
|------|-------|----------------|
| `benchmarks/vector-db/run_benchmark.py` | 1 | Benchmark orchestrator, CLI args |
| `benchmarks/rag-framework/evaluate.py` | 2 | Framework evaluator, comparison tables |
| `benchmarks/rag-framework/frameworks/*/pipeline.py` | 2 | Individual framework PoC |
| `benchmarks/embedding-model/evaluate.py` | 3 | Model evaluator, retrieval quality, weighted scorecard |
| `benchmarks/embedding-model/models/*.py` | 3 | Individual embedding model adapter |
| `benchmarks/llm-provider/evaluate.py` | 3.5 | Provider evaluator, answer quality, weighted scorecard |
| `benchmarks/llm-provider/providers/*.py` | 3.5 | Individual LLM provider adapter |
| `api/main.py` | 4 | FastAPI app, route registration, OpenAPI schema |
| `api/routes/auth_routes.py` | 4 | `/api/v1/auth/token` — JWT login |
| `api/routes/chat.py` | 4 | `/api/v1/chat/completions` — RAG endpoint (with error handling) |
| `api/routes/documents.py` | 4 | `/api/v1/documents/*` — document management |
| `api/routes/webhooks/line.py` | 4 | `/api/v1/webhooks/line` — LINE adapter |
| `tests/integration/conftest.py` | 5 | Pytest fixtures (TestClient, auth tokens) |
| `tests/integration/test_scenarios.py` | 5 | 27 E2E tests across 7 scenarios |
| `tests/load/locustfile.py` | 5 | Locust load test (EmployeeUser + CustomerUser) |
| `pyproject.toml` | 1-5 | Root project config, uv dependency groups |
| `Makefile` | 1-5 | All make targets (wraps `uv sync` + runner commands) |

## Anti-Lock-in Strategy

Both phases apply the same pattern:
- **Port:** Abstract base class (`VectorDBClient`, `BaseRAGPipeline`)
- **Adapter:** One concrete class per vendor/framework
- **Rule:** Swap component = change 1 class, zero orchestrator changes

## Extension Points

**Add new Vector DB (Phase 1):**
1. `clients/mydb.py` inheriting `VectorDBClient`
2. Add to `CLIENTS_MAP` in `run_benchmark.py`
3. Add Docker service to `docker-compose.vector-db.yml`

**Add new RAG Framework (Phase 2):**
1. `frameworks/myfw/pipeline.py` inheriting `BaseRAGPipeline`
2. Add to `FRAMEWORK_REGISTRY` in `evaluate.py`
3. No changes to evaluator logic

**Add new Embedding Model (Phase 3):**
1. `models/mymodel.py` inheriting `BaseEmbeddingModel`
2. Implement `_encode_raw()` and `meta` property
3. Add to `MODEL_REGISTRY` in `evaluate.py`
4. For query/passage prefix models: add `encode_queries()` / `encode_passages()` methods

**Add new LLM Provider (Phase 3.5):**
1. `providers/myprovider.py` inheriting `BaseLLMProvider`
2. Implement `_generate_raw(prompt, context)` → `(text, input_tokens, output_tokens)`
3. Implement `meta` property with `ProviderMeta`
4. Add to `PROVIDER_REGISTRY` in `evaluate.py`
5. Update `.env.example` with provider-specific API keys

## Related Files

- `plan.md` — Full 6-phase spike plan (Phases 4–6 not yet started)
- `datasets/` — Thai/English/Mixed test documents (reused Phases 2–3.5)
- `.env.example` — Environment variables template
- `benchmarks/embedding-model/results/` — Phase 3 JSON output with rankings
- `benchmarks/llm-provider/results/` — Phase 3.5 JSON output with rankings
