<!-- Generated: 2026-03-31 | Files scanned: 38 | Token estimate: ~400 -->

# RAG Spike Codemaps Index

**Last Updated:** 2026-03-31 | **Project Phase:** 1 ✅ Vector DB | 2 🔄 RAG Framework | 3 🔄 Embedding Models

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
│   └── embedding-model/                  # [Phase 3 🔄]
│       ├── evaluate.py                   # Retrieval quality + weighted scorecard
│       ├── base.py                       # BaseEmbeddingModel ABC
│       ├── config.py                     # Chunk settings, paths
│       ├── requirements.txt
│       ├── models/
│       │   ├── bge_m3.py                # BAAI/bge-m3 (multilingual)
│       │   ├── multilingual_e5.py       # intfloat/multilingual-e5-large
│       │   ├── mxbai.py                 # mixedbread-ai/mxbai-embed-large-v1
│       │   ├── openai_large.py          # text-embedding-3-large
│       │   └── openai_small.py          # text-embedding-3-small
│       └── results/                     # embedding_model_results.json
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
| 3.5 | LLM Provider Comparison | ⏳ Not started | Cost/quality tradeoffs |
| 4 | API Layer & Auth Design | ⏳ Not started | FastAPI + JWT + RBAC |
| 5 | Integration Testing | ⏳ Not started | End-to-end pipeline |
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
```

---

## Key Design Principle

Both benchmarks use **Port & Adapter pattern**:
- Abstract base class defines the interface
- Concrete implementations are swappable
- Orchestrator never touches DB/framework-specific code

This ensures the final architecture recommendation is based on evidence, not vendor preference.
