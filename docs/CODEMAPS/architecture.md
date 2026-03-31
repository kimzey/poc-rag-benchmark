<!-- Generated: 2026-03-31 | Files scanned: 9 | Token estimate: ~650 -->

# Architecture Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 (Vector DB Evaluation)

## Overview

RAG spike Phase 1 evaluates 4 vector databases using a **Port & Adapter pattern** to maximize portability. The benchmark measures indexing speed, query latency, filtering overhead, and recall accuracy across Qdrant, pgvector, Milvus, and OpenSearch.

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│  run_benchmark.py                                       │
│  ├─ Argument parsing (--db, --n, --skip)               │
│  ├─ Dataset generation (10K-100K vectors)              │
│  └─ Orchestration: connect → insert → search → measure │
└─────────────────────────────────────────────────────────┘
           │
           ├─ (A) Synthetic Data Generation
           │       dataset.py → unit-norm vectors (dim=1536)
           │       metadata: access_level, category, source
           │       ground truth: brute-force exact kNN (for recall)
           │
           ├─ (B) Port & Adapter Pattern [ANTI-LOCK-IN]
           │
           │   VectorDBClient (ABC)
           │   ├─ name: str
           │   ├─ connect() → None
           │   ├─ create_collection(name) → None
           │   ├─ insert(records[BenchmarkRecord]) → None
           │   ├─ search(vector, top_k, filter?) → [SearchResult]
           │   ├─ count() → int
           │   └─ drop_collection() → None
           │
           │   Implementations:
           │   ├─ QdrantAdapter    (Qdrant REST/gRPC)
           │   ├─ PgvectorAdapter  (PostgreSQL + pgvector)
           │   ├─ MilvusAdapter    (Milvus gRPC)
           │   └─ OpenSearchAdapter (OpenSearch HTTP)
           │
           └─ (C) Metrics & Results
                   metrics.py → LatencyStats, BenchmarkResult
                   (p50, p95, p99 latency; QPS; recall@10)
```

## Key Design Patterns

### 1. **Port & Adapter (Hexagonal Architecture)**

- **Port:** `VectorDBClient` abstract interface
  - 6 required methods: connect, create_collection, insert, search, count, drop_collection
  - Decouples benchmark logic from DB-specific implementations
  - **Anti-lock-in benefit:** Swap backends without touching benchmark code

- **Adapters:** 4 concrete implementations
  - Each adapter translates BenchmarkRecord → DB schema
  - Each adapter translates DB response → SearchResult
  - Can drop/add adapters with zero changes to orchestrator

### 2. **Synthetic Data with Metadata**

- Vectors: unit-normalized Gaussian (shape: N × 1536)
- Metadata fields (test permission filtering):
  - `access_level`: public (50%) | internal (35%) | confidential (15%)
  - `category`: tech (40%) | hr (20%) | finance (20%) | ops (20%)
  - `source`: doc_{id} (traceability)

### 3. **Filtered Search Overhead Measurement**

Benchmarks include both:
1. **ANN search** (no filter) → baseline latency
2. **Filtered ANN** (access_level=internal) → production-realistic overhead

Both measure p50/p95/p99 latency & QPS.

## Entry Points

| File | Purpose | Responsibility |
|------|---------|-----------------|
| `run_benchmark.py` | Benchmark orchestrator | Argument parsing, client selection, summary reporting |
| `clients/base.py` | Abstract interface | Defines VectorDBClient protocol + data classes |
| `clients/{qdrant,pgvector,milvus,opensearch}.py` | Adapters | DB-specific connection, schema, query translation |
| `utils/dataset.py` | Data generation | Synthetic vectors + metadata, brute-force ground truth |
| `utils/metrics.py` | Measurement | Latency stats, recall computation, JSON export |

## Data Flow

1. **Generate** → `generate_dataset(n)` → list[BenchmarkRecord]
2. **Generate queries** → `generate_queries(n)` → list[vector]
3. **Ground truth** → `compute_ground_truth()` → list[set[doc_ids]] (only for n ≤ 50K)
4. **For each DB:**
   - Client instantiation (host/port from defaults)
   - `connect()` → establish connection
   - `create_collection()` → schema + indexes
   - `insert(dataset)` → measure index throughput
   - `search(query, top_k=10, filter?)` → measure latency (100 runs)
   - `count()` → verify insertion
   - `drop_collection()` → cleanup
5. **Summarize** → Rich table: DB, vectors, latency percentiles, QPS, recall

## Related Files

- `Makefile` — Build targets: `up-db`, `benchmark-quick`, `benchmark-all`
- `docker-compose.vector-db.yml` — Container definitions (5 services + 2 etcd/minio deps)
- `plan.md` — Full 6-phase spike research plan
- `benchmarks/vector-db/results/` — JSON output of each run (timestamped)

---

## Extension Points

To add a new vector DB:

1. Create `clients/mynewdb.py` inheriting from `VectorDBClient`
2. Implement 6 required methods
3. Add to `CLIENTS_MAP` in `run_benchmark.py`
4. Add Docker service to `docker-compose.vector-db.yml`
5. Test: `python run_benchmark.py --db mynewdb`

No changes to orchestrator logic needed.
