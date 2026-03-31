<!-- Generated: 2026-03-31 | Files scanned: 3 | Token estimate: ~480 -->

# Data Schema & Generation Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 (Vector DB Evaluation)

## BenchmarkRecord Schema

The core data structure passed to all vector DBs.

```python
@dataclass
class BenchmarkRecord:
    id: str                      # Unique document ID
    vector: list[float]          # Embedding (dim=1536)
    metadata: dict               # {access_level, category, source}
```

| Field | Type | Purpose | Constraints |
|-------|------|---------|-------------|
| `id` | str | Document identifier | Sequential (0, 1, 2, ..., n-1) |
| `vector` | list[float] | Embedding vector | dim=1536 (OpenAI text-embedding-3-small) |
| `metadata.access_level` | str | Permission level | public \| internal \| confidential |
| `metadata.category` | str | Document type | tech \| hr \| finance \| ops |
| `metadata.source` | str | Document source | doc_{id:06d} (e.g., doc_000042) |

## Vector Generation

**Function:** `dataset.py:generate_dataset(n, dim=1536, seed=42)`

```python
# Algorithm:
1. np.random.default_rng(seed).standard_normal((n, dim))     # Gaussian noise
2. Normalize each row to unit length (L2 norm)               # Enables cosine similarity = dot product
3. Convert to list[float] for JSON serialization
```

**Properties:**
- Shape: (n_vectors, 1536)
- Distribution: Unit-normalized Gaussian (isotropic)
- Seed: 42 (deterministic, reproducible)
- Type: float32 (memory-efficient)
- Similarity metric: Cosine distance (all DBs use this)

## Metadata Generation

**Probability distributions (realistic production skew):**

```python
ACCESS_LEVELS = ["public", "internal", "confidential"]
ACCESS_WEIGHTS = [0.5, 0.35, 0.15]      # Real-world access skew
                  # 50% public, 35% internal, 15% confidential

CATEGORIES = ["tech", "hr", "finance", "ops"]
CATEGORY_WEIGHTS = [0.4, 0.2, 0.2, 0.2]  # Tech-heavy org
```

**Assignment:** Independent random choice per record (no correlation).

**Schema mapping per database:**

| DB | id → | vector → | access_level → | category → | source → |
|----|------|----------|-----------------|-----------|----------|
| **Qdrant** | PointStruct.id | payload | payload | payload | payload |
| **pgvector** | BIGINT PK | vector column | TEXT | TEXT | TEXT |
| **Milvus** | INT64 PK | FLOAT_VECTOR | VARCHAR(32) | VARCHAR(64) | VARCHAR(256) |
| **OpenSearch** | _id | embedding field | keyword | keyword | keyword |

## Query Generation

**Function:** `dataset.py:generate_queries(n, dim=1536, seed=99)`

Same algorithm as vectors:
1. Gaussian noise
2. Unit normalization
3. Seed: 99 (separate from dataset seed)

**Usage:** 
- First 100 queries → ANN search latency measurement
- Next 50 queries → Filtered search latency measurement
- Same queries used for all DBs (consistency)

## Ground Truth Computation

**Function:** `dataset.py:compute_ground_truth(dataset, queries, top_k=10)`

```python
# Algorithm: Brute-force exact nearest neighbors
corpus = np.array([r.vector for r in dataset])      # (n, 1536)
queries = np.array(queries)                         # (q, 1536)
scores = queries @ corpus.T                         # (q, n) via cosine similarity
top_ids = argpartition(scores, -k)[-k:]             # exact top-k
return list[set[str]]                               # ground truth per query
```

**Complexity:** O(n * q) — only feasible for n ≤ 50K

**Purpose:** Compute recall@10
- Exact ranking from brute-force
- Compare each DB's ANN results against it
- Recall = (hits in top-10) / (10 * num_queries)

**Note:** Skipped for n > 50K (too slow; ground truth omitted from results).

## SearchResult Schema

Returned by all adapters after search.

```python
@dataclass
class SearchResult:
    id: str                      # Document ID from result
    score: float                 # Similarity score (0.0–1.0 for cosine)
    metadata: dict               # {access_level, category, source}
```

## LatencyStats Schema

Aggregated per-query latency metrics.

```python
@dataclass
class LatencyStats:
    p50_ms: float                # Median latency (milliseconds)
    p95_ms: float                # 95th percentile
    p99_ms: float                # 99th percentile
    mean_ms: float               # Arithmetic mean
    qps: float                   # Queries per second = count / total_time_s
```

**Computation:** `metrics.py:measure_latencies(times_ms)`
- Input: list of query times (in ms)
- Output: LatencyStats
- Uses numpy.percentile (supports arbitrary quantiles)

## BenchmarkResult Schema

Final output saved to JSON.

```python
@dataclass
class BenchmarkResult:
    db_name: str                 # e.g., "Qdrant"
    n_vectors: int               # Dataset size
    dim: int                      # Vector dimension (always 1536)
    index_time_s: float           # Total indexing time
    index_throughput: float       # vectors/second
    search_latency: LatencyStats  # ANN search (no filter)
    filtered_latency: LatencyStats | None  # Filtered search (if supported)
    recall_at_10: float | None    # Recall metric (None if n > 50K)
    notes: str = ""               # Optional notes
```

## Dataset Sizes

| Name | Vectors | Use Case |
|------|---------|----------|
| Quick | 10,000 | Fast iteration, dev testing |
| Medium | 100,000 | Production-scale realism |
| Large | (planned Phase 2) | 1M+ vectors |

**Command:**
```bash
make benchmark-quick     # 10K (≈30s on mid-tier hardware)
make benchmark-medium    # 100K (≈3min)
make benchmark-all       # both
```

## Reproducibility

- Fixed seeds (42 for data, 99 for queries)
- Same dataset/queries used across all DBs
- No randomization in benchmark loop (only measurement)
- Results JSON timestamped: `results_{timestamp}.json`
