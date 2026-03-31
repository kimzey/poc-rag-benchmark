<!-- Generated: 2026-03-31 | Files scanned: 29 | Token estimate: ~850 -->

# Architecture Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 ✅ + 2 🔄 (RAG Framework Comparison)

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
└── [Phase 2 🔄] RAG Framework Comparison ─────────────────────────
    benchmarks/rag-framework/evaluate.py
      └─ BaseRAGPipeline (ABC)
          ├─ BareMetalRAGPipeline   (numpy cosine + direct OpenRouter)
          ├─ LlamaIndexRAGPipeline  (VectorStoreIndex, global Settings)
          ├─ LangChainRAGPipeline   (FAISS, RetrievalQA chain)
          └─ HaystackRAGPipeline    (DAG pipeline, InMemoryDocumentStore)
    Data: Thai + English + Mixed documents (3 docs, 10 questions)
    LLM: OpenRouter (configurable model)
    Embeddings: sentence-transformers (local, no API key)
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

## Entry Points

| File | Phase | Responsibility |
|------|-------|----------------|
| `benchmarks/vector-db/run_benchmark.py` | 1 | Benchmark orchestrator, CLI args |
| `benchmarks/rag-framework/evaluate.py` | 2 | Framework evaluator, comparison tables |
| `benchmarks/rag-framework/frameworks/*/pipeline.py` | 2 | Individual framework PoC |
| `Makefile` | Both | `make benchmark-*`, `make rag-eval*` |

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

## Related Files

- `plan.md` — Full 6-phase spike plan (Phases 3–6 not yet started)
- `datasets/` — Thai/English/Mixed test documents for Phase 2
- `.env.example` — Environment variables template
