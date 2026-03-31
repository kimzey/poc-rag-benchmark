<!-- Generated: 2026-03-31 | Files scanned: 15 | Token estimate: ~250 -->

# RAG Spike Codemaps Index

**Last Updated:** 2026-03-31 | **Project Phase:** 1 (Vector DB Evaluation)

## Quick Navigation

This directory contains architectural maps of the RAG spike research project. Start here to understand code structure before diving into implementation.

## Codemaps

### [architecture.md](./architecture.md)
**Port & Adapter pattern, benchmark orchestration, design rationale**

- System diagram: benchmark flow end-to-end
- Abstract `VectorDBClient` interface (6 methods)
- 4 concrete adapters: Qdrant, pgvector, Milvus, OpenSearch
- Anti-lock-in strategy (swap DBs without code changes)
- Data flow: generation → insertion → search → measurement
- Extension points for new vector DBs

**Read this to understand:** How benchmarks work, where to add a new DB adapter

---

### [data.md](./data.md)
**BenchmarkRecord schema, synthetic data generation, ground truth**

- BenchmarkRecord: id, vector (dim=1536), metadata (access_level, category, source)
- Vector generation: unit-normalized Gaussian, deterministic seed (42)
- Metadata: realistic probability skew (50% public, 35% internal, 15% confidential)
- Query generation: separate seed (99) for 150 query vectors
- Ground truth: brute-force exact kNN (numpy, O(n*q), only n ≤ 50K)
- Latency/Recall metrics: p50/p95/p99 latency, QPS, recall@10
- Dataset sizes: 10K (quick), 100K (medium), 1M+ (planned)

**Read this to understand:** Data schema for each DB, reproducibility guarantees, metric definitions

---

### [dependencies.md](./dependencies.md)
**Python packages, Docker infrastructure, hardware requirements**

- 5 DB client libraries (qdrant-client, psycopg2, pgvector, pymilvus, opensearch-py)
- 4 utility packages (numpy, rich, tqdm, python-dotenv)
- 5 Docker services + 2 dependencies (Milvus needs etcd + minio)
- Ports: Qdrant 6333, PostgreSQL 5433, Milvus 19530, OpenSearch 9200
- Volume management: persistent data directories
- Build targets: make up-db, make install, make benchmark-*
- Hardware: 4+ cores, 8GB+ RAM, 10GB+ disk

**Read this to understand:** Environment setup, Docker stack architecture, infrastructure dependencies

---

## Project Structure

```
spike-rak/
├── plan.md                          # Full 6-phase spike plan
├── Makefile                         # make up-db, make benchmark-quick, etc.
├── docker/
│   └── docker-compose.vector-db.yml # 5 services (qdrant, pgvector, milvus, opensearch, etcd, minio)
├── benchmarks/vector-db/
│   ├── run_benchmark.py             # Benchmark orchestrator
│   ├── requirements.txt              # Python dependencies
│   ├── clients/
│   │   ├── base.py                  # VectorDBClient ABC
│   │   ├── qdrant.py                # Qdrant adapter
│   │   ├── pgvector.py              # PostgreSQL adapter
│   │   ├── milvus.py                # Milvus adapter
│   │   └── opensearch.py            # OpenSearch adapter
│   ├── utils/
│   │   ├── dataset.py               # Vector & query generation, ground truth
│   │   └── metrics.py               # Latency stats, recall, JSON export
│   └── results/                     # Timestamped benchmark JSON files
└── docs/
    └── CODEMAPS/                    # You are here
        ├── INDEX.md                 # This file
        ├── architecture.md          # System design
        ├── data.md                  # Data schema
        └── dependencies.md          # Infrastructure
```

## Common Tasks

### Set up environment and run a quick benchmark

```bash
# Install Python dependencies
make install

# Start all vector DBs in Docker
make up-db

# Run benchmark (10K vectors, all DBs)
make benchmark-quick

# Stop & cleanup
make down-db
```

### Run benchmark for a specific database

```bash
make benchmark-db DB=qdrant N=50000
```

Databases: `qdrant`, `pgvector`, `milvus`, `opensearch`

### Understand benchmark output

Results table shows per-DB:
- **Vectors:** Dataset size
- **Index time (s):** Total indexing duration
- **Throughput (v/s):** Vectors indexed per second
- **Search p50/p95/p99 (ms):** Latency percentiles for ANN queries
- **Search QPS:** Queries per second (100 queries measured)
- **Filter p95 (ms):** Latency for filtered search (if supported)
- **Recall@10:** Ratio of correct results in top-10 vs. ground truth

### Add a new vector database

1. Create `benchmarks/vector-db/clients/mydb.py`
2. Inherit from `VectorDBClient`
3. Implement: `connect()`, `create_collection()`, `insert()`, `search()`, `count()`, `drop_collection()`
4. Add entry to `CLIENTS_MAP` in `run_benchmark.py`
5. Add Docker service to `docker/docker-compose.vector-db.yml`
6. Test: `python run_benchmark.py --list` (should show your DB)

## Key Insights

### Design Pattern: Port & Adapter
Benchmark code knows only the `VectorDBClient` interface. Each DB (Qdrant, pgvector, Milvus, OpenSearch) is an adapter. Swapping DBs requires zero changes to benchmark logic — adds new file, updates config, done.

### Data Generation: Reproducible & Production-Realistic
- Vectors: unit-normalized Gaussian (cosine similarity = dot product)
- Metadata: Skewed probability (50% public vs 15% confidential) mirrors real permission control
- Filtered search benchmark directly measures permission-check overhead

### Metrics: Latency Percentiles + Recall
- Latency: p50, p95, p99 (+ mean, QPS) — typical SLOs are p95/p99
- Recall@10: Exact ranking vs. ANN ranking (brute-force ground truth)
- Both matter: a DB may be fast but approximate; need both dimensions

### No Lock-In
After Phase 1, project can:
- Drop a DB without refactoring
- Add multi-DB hybrid (use Qdrant for speed, Milvus for cost)
- Swap cloud vendors (e.g., AWS OpenSearch → managed Qdrant)

---

## Phase Context

This is **Phase 1 (Vector DB Evaluation)** of a 6-phase RAG spike:
1. **Vector DB benchmark** ← YOU ARE HERE
2. Integration with embedding models
3. Basic RAG pipeline (retrieval + generation)
4. Production scaling & cost analysis
5. Advanced filtering & re-ranking
6. Multi-modal support (images, PDFs, video)

Each phase adds features; Phase 1's adapter pattern ensures later phases stay portable.

---

**Questions?** Check the individual codemaps or the full spike plan in `plan.md`.
