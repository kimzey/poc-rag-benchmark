<!-- Generated: 2026-03-31 | Files scanned: 2 | Token estimate: ~420 -->

# Dependencies & Infrastructure Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 (Vector DB Evaluation)

## Python Packages

**File:** `benchmarks/vector-db/requirements.txt`

### Vector DB Clients

| Package | Version | Purpose | Adapter | Usage |
|---------|---------|---------|---------|-------|
| `qdrant-client` | ≥1.9.0 | Qdrant SDK | QdrantAdapter | REST API + gRPC to Qdrant |
| `psycopg2-binary` | ≥2.9.9 | PostgreSQL adapter | PgvectorAdapter | JDBC-like connection pool |
| `pgvector` | ≥0.2.5 | PostgreSQL vector type | PgvectorAdapter | Serialize vectors in SQL |
| `pymilvus` | ≥2.4.0 | Milvus SDK | MilvusAdapter | gRPC connection + schema API |
| `opensearch-py` | ≥2.5.0 | OpenSearch SDK | OpenSearchAdapter | HTTP bulk indexing + search |

### Utilities

| Package | Version | Purpose | Used By |
|---------|---------|---------|---------|
| `numpy` | ≥1.26.0 | Numerical computation | dataset.py (vector gen, ground truth) |
| `tqdm` | ≥4.66.0 | Progress bars | (optional, not currently used) |
| `rich` | ≥13.7.0 | Terminal UI | run_benchmark.py (tables, colors, spinners) |
| `python-dotenv` | ≥1.0.0 | Environment config | (optional, for .env override) |

**Total:** 12 packages (5 DB clients + 4 utilities + 3 deps)

## Docker Infrastructure

**File:** `docker/docker-compose.vector-db.yml`

All services accessible on `localhost`:

### Qdrant

```yaml
Image:         qdrant/qdrant:v1.9.2
Container:     spike_qdrant
Ports:         6333 (REST), 6334 (gRPC)
Storage:       qdrant_data/
Healthcheck:   curl http://localhost:6333/healthz
```

**Adapter config:** `QdrantAdapter(host="localhost", port=6333)`

### PostgreSQL + pgvector

```yaml
Image:         pgvector/pgvector:pg16
Container:     spike_pgvector
Ports:         5433 (local) → 5432 (container)
Database:      vectordb
Credentials:   user=spike, password=spike
Storage:       pgvector_data/
Healthcheck:   pg_isready -U spike -d vectordb
```

**Adapter config:** `PgvectorAdapter(host="localhost", port=5433, ...)`

**Schema example:**
```sql
CREATE TABLE spike_benchmark (
    id          BIGINT PRIMARY KEY,
    embedding   vector(1536),
    access_level TEXT,
    category    TEXT,
    source      TEXT
);
CREATE INDEX USING hnsw (embedding vector_cosine_ops);
```

### Milvus

**Dependency tree:**
```
Milvus ←── etcd (coordination)
       ←── minio (object storage)
```

```yaml
Milvus:
  Image:     milvusdb/milvus:v2.4.5
  Container: spike_milvus
  Ports:     19530 (gRPC), 9091 (metrics)
  Depends:   etcd (healthy), minio (healthy)
  Storage:   milvus_data/

etcd:
  Image:     quay.io/coreos/etcd:v3.5.5
  Container: spike_etcd
  Port:      2379 (internal only)
  Storage:   etcd_data/

minio:
  Image:     minio/minio:2023-03-20
  Container: spike_minio
  Port:      9000 (API), 9001 (console)
  Storage:   minio_data/
```

**Adapter config:** `MilvusAdapter(host="localhost", port=19530)`

### OpenSearch

```yaml
Image:         opensearchproject/opensearch:2.13.0
Container:     spike_opensearch
Ports:         9200 (API), 9600 (performance analyzer)
Storage:       opensearch_data/
Memory:        512m min/max (configurable)
Features:      KNN plugin, security disabled (dev only)
Healthcheck:   curl http://localhost:9200/_cluster/health
```

**Adapter config:** `OpenSearchAdapter(host="localhost", port=9200)`

## Volume Management

Persistent storage for all services:

| Volume | Service | Mount Point |
|--------|---------|-------------|
| `qdrant_data` | Qdrant | /qdrant/storage |
| `pgvector_data` | PostgreSQL | /var/lib/postgresql/data |
| `etcd_data` | etcd | /etcd |
| `minio_data` | MinIO | /minio_data |
| `milvus_data` | Milvus | /var/lib/milvus |
| `opensearch_data` | OpenSearch | /usr/share/opensearch/data |

**Cleanup:**
```bash
make down-db    # docker compose down -v (removes all volumes)
```

## Build & Run Commands

**Install Python dependencies:**
```bash
make install
# → pip install -r benchmarks/vector-db/requirements.txt
```

**Start all vector DBs:**
```bash
make up-db
# → docker compose -f docker/docker-compose.vector-db.yml up -d
```

**Start single DB (e.g., Qdrant):**
```bash
make up-db DB=qdrant
```

**Run benchmark:**
```bash
make benchmark-quick              # 10K vectors (≈30s)
make benchmark-medium             # 100K vectors (≈3min)
make benchmark-all                # both
make benchmark-db DB=qdrant N=50000  # custom
```

**Stop & cleanup:**
```bash
make down-db    # Stop containers + remove volumes
```

**View logs:**
```bash
make logs-db              # All services
make logs-db DB=qdrant    # Single service
```

## Hardware Requirements

Tested on:
- **CPU:** 4+ cores
- **RAM:** 8GB+ (Milvus + OpenSearch require ≥2GB each)
- **Disk:** 10GB+ (for volumes)

**Estimated runtime:**
- 10K vectors: 20–40s (all adapters)
- 100K vectors: 2–5min (all adapters)

## Network Topology

```
localhost:6333 ←→ Qdrant
localhost:5433 ←→ PostgreSQL
localhost:19530 ←→ Milvus (gRPC)
localhost:9200 ←→ OpenSearch (HTTP)

Internal (not exposed):
localhost:2379 ← etcd (Milvus only)
localhost:9000 ← MinIO (Milvus only)
```

All services isolated in Docker network. Use service names (`qdrant`, `milvus`, etc.) for container-to-container communication.

## Environment Variables

Optional `.env` file (loaded by python-dotenv):

```bash
# Override defaults
QDRANT_HOST=localhost
QDRANT_PORT=6333

PGVECTOR_HOST=localhost
PGVECTOR_PORT=5433
PGVECTOR_USER=spike
PGVECTOR_PASSWORD=spike

MILVUS_HOST=localhost
MILVUS_PORT=19530

OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

Currently hardcoded in adapters; .env support is placeholder for Phase 2.

---

**Next Steps (Phase 2+):**
- Cloud deployments (AWS, GCP managed vector services)
- Kubernetes ingress (if scale testing added)
- Secrets management (vault, AWS Secrets Manager)
