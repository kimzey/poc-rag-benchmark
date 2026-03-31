<!-- Generated: 2026-03-31 | Files scanned: 12 | Token estimate: ~750 -->

# Data Schema & Generation Codemap

**Last Updated:** 2026-03-31 | **Phase:** 1 ✅ + 2 🔄 + 3 🔄 + 3.5 🆕

---

## Phase 1 — Synthetic Vector Dataset

### BenchmarkRecord

```python
@dataclass
class BenchmarkRecord:
    id: str               # Sequential: "0", "1", ..., "n-1"
    vector: list[float]   # dim=1536, unit-normalized
    metadata: dict        # {access_level, category, source}
```

### Generation — `utils/dataset.py`

```
generate_dataset(n, dim=1536, seed=42)
  → np.random.default_rng(42).standard_normal((n, 1536))
  → L2-normalize each row
  → metadata: random choice with weights below
```

**Metadata distributions:**

| Field | Values | Weights |
|-------|--------|---------|
| `access_level` | public / internal / confidential | 50% / 35% / 15% |
| `category` | tech / hr / finance / ops | 40% / 20% / 20% / 20% |
| `source` | doc_{id:06d} | sequential |

### Query Generation — `utils/dataset.py`

```
generate_queries(n, dim=1536, seed=99)  # separate seed from data
  → same algorithm as dataset
  → first 100: ANN latency measurement
  → next 50: filtered search measurement
```

### Ground Truth

```
compute_ground_truth(dataset, queries, top_k=10)
  → brute-force exact kNN via matrix multiply (O(n*q))
  → only computed when n ≤ 50K (performance gate)
  → output: list[set[str]] — expected doc IDs per query
```

### SearchResult / Metrics

```python
@dataclass
class SearchResult:
    id: str; score: float; metadata: dict

@dataclass
class LatencyStats:
    p50_ms: float; p95_ms: float; p99_ms: float; mean_ms: float; qps: float

@dataclass
class BenchmarkResult:
    db_name: str; n_vectors: int; dim: int
    index_time_s: float; index_throughput: float
    search_latency: LatencyStats
    filtered_latency: LatencyStats | None
    recall_at_10: float | None
```

### Dataset Sizes

| Name | Vectors | Runtime |
|------|---------|---------|
| Quick | 10,000 | ~30s |
| Medium | 100,000 | ~3min |

---

## Phase 2 — Real-World Document Dataset

### Documents — `datasets/`

| File | Language | Content | Size |
|------|----------|---------|------|
| `hr_policy_th.md` | Thai | HR policy: leave, WFH, OT, probation, benefits, performance review | ~200 lines |
| `tech_docs_en.md` | English | Internal API docs: endpoints, auth, rate limits, webhooks, error codes | ~180 lines |
| `faq_mixed.md` | Thai + English | FAQ covering API usage, HR questions, security, internal tools | ~170 lines |

**Content notes:**
- `hr_policy_th.md`: วันลาพักร้อน 10 วัน (15 วันที่ 3 ปี, 20 วันที่ 5 ปี), WFH 2 วัน/สัปดาห์, Probation 3 เดือน
- `tech_docs_en.md`: REST API v1.0, Employee/Customer/Service tokens, rate limits 30–500 req/min
- `faq_mixed.md`: Cross-references both documents, practical Q&A format

### Test Questions — `datasets/questions.json`

10 questions across 4 categories:

| ID | Category | Language | Source Doc |
|----|----------|----------|-----------|
| 1–2 | `thai_hr` | Thai | hr_policy_th.md |
| 3–4 | `thai_hr` | Thai | hr_policy_th.md |
| 5–6 | `english_api` | English | tech_docs_en.md |
| 7 | `english_api` | English | faq_mixed + tech_docs |
| 8 | `thai_mixed` | Thai | hr_policy + faq_mixed |
| 9 | `thai_mixed` | Thai | hr_policy + faq_mixed |
| 10 | `english_security` | English | faq_mixed.md |

Schema per question:
```json
{
  "id": 1,
  "question": "พนักงานทั่วไปมีวันลาพักร้อนกี่วันต่อปี?",
  "category": "thai_hr",
  "source_doc": "hr_policy_th.md",
  "expected_answer": "10 วันต่อปี"
}
```

### Phase 2 Data Flow

```
datasets/*.md files
    │
    ▼  build_index()
chunk (word-based, size=500, overlap=50)
    │
    ▼  sentence-transformers
embedding vectors (dim=384 for all-MiniLM-L6-v2)
    │
    ▼  framework-specific store
in-memory vector store (FAISS / VectorStoreIndex / InMemoryDocumentStore / numpy)
    │
    ▼  query()
embed question → cosine retrieve top_k=3 → LLM generate (OpenRouter)
    │
    ▼
RAGResult: {answer, sources, latency_ms, retrieved_chunks}
```

### IndexStats / RAGResult

```python
@dataclass
class IndexStats:
    num_chunks: int         # Total chunks across all documents
    indexing_time_ms: float # Wall-clock time for full build_index()
    framework: str

@dataclass
class RAGResult:
    answer: str             # LLM-generated answer
    sources: list[str]      # File paths of retrieved chunks
    latency_ms: float       # End-to-end query time
    retrieved_chunks: list[str]  # Raw chunk text
```

### Output — `benchmarks/rag-framework/results/`

Results saved as `rag_framework_results.json`:
```json
{
  "phase": 2,
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_model": "anthropic/claude-3-haiku",
  "chunk_size": 500,
  "results": [
    {
      "framework": "bare_metal",
      "num_chunks": 42,
      "indexing_time_ms": 1240,
      "loc": 78,
      "queries": [...]
    }
  ]
}
```

---

## Phase 3 — Embedding Model Benchmark Data

### EmbedResult

```python
@dataclass
class EmbedResult:
    embeddings: np.ndarray      # shape (n, dims), L2-normalized
    latency_ms: float           # total wall time
```

### ModelMeta

```python
@dataclass
class ModelMeta:
    name: str                           # e.g. "BAAI/bge-m3"
    dimensions: int                     # embedding vector size
    max_tokens: int                     # context length
    cost_per_1m_tokens: float          # USD; 0.0 for open-source
    vendor_lock_in: int                # 0 (open) to 10 (locked)
    self_hostable: bool                # Can run locally
```

### Corpus — Phase 3 Reuses Phase 2 Documents

Same 3 documents (hr_policy_th.md, tech_docs_en.md, faq_mixed.md), chunked with chunk_size=500, overlap=50

Corpus: ~42 chunks across 3 documents (same as Phase 2)

### Test Questions

Same 10 questions from Phase 2 questions.json:
- Thai HR (2)
- Thai HR (2)
- English API (2)
- English API (1 with cross-doc)
- Thai Mixed (2)
- English Security (1)

**Ground truth:** Token overlap (Jaccard) of expected_answer vs corpus chunks

### Query Result Structure (Phase 3)

```json
{
  "id": 1,
  "question": "...",
  "category": "thai_hr",
  "gt_chunk_idx": 5,
  "hit_at_k": true,
  "reciprocal_rank": 0.5,
  "retrieved_top1_chunk": "...",
  "query_latency_ms": 12.3
}
```

### Output — `benchmarks/embedding-model/results/embedding_model_results.json`

```json
{
  "phase": 3,
  "top_k": 3,
  "chunk_size": 500,
  "chunk_overlap": 50,
  "num_chunks": 42,
  "num_questions": 10,
  "weights": {
    "thai_recall": 0.25,
    "eng_recall": 0.15,
    "latency": 0.15,
    "cost": 0.15,
    "self_host": 0.10,
    "dimension": 0.05,
    "max_tokens": 0.05,
    "lock_in": 0.10
  },
  "results": [
    {
      "model": "bge_m3",
      "meta": {
        "name": "BAAI/bge-m3",
        "dimensions": 1024,
        "max_tokens": 8192,
        "cost_per_1m_tokens": 0.0,
        "vendor_lock_in": 0,
        "self_hostable": true
      },
      "index_time_ms": 245.0,
      "avg_query_latency_ms": 18.5,
      "thai_recall": 1.0,
      "eng_recall": 0.857,
      "overall_recall": 0.9,
      "mrr": 0.783,
      "weighted_score": 0.8234,
      "queries": [...]
    }
  ]
}
```

**Ranking:** Results sorted by `weighted_score` (highest first); rank 1 = "⭐ RECOMMENDED"

---

## Phase 3.5 — LLM Provider Benchmark Data

### GenerateResult

```python
@dataclass
class GenerateResult:
    text: str               # Generated answer text
    latency_ms: float       # Wall time for the full response
    input_tokens: int       # Prompt tokens consumed
    output_tokens: int      # Completion tokens generated
    cost_usd: float         # Estimated cost in USD for this call
```

### ProviderMeta

```python
@dataclass
class ProviderMeta:
    name: str               # e.g. "OpenRouter / gpt-4o-mini"
    model_id: str           # API model string (e.g. "openai/gpt-4o-mini")
    provider: str           # "openrouter" | "openai" | "anthropic" | "ollama"
    cost_per_1m_input: float    # USD per 1M input tokens; 0.0 for self-hosted
    cost_per_1m_output: float   # USD per 1M output tokens; 0.0 for self-hosted
    vendor_lock_in: int     # 0 (fully open) to 10 (hard lock-in)
    self_hostable: bool     # Can run locally without cloud API
    openai_compatible: bool # Uses OpenAI-compatible API endpoint
```

### Corpus & Questions

Same 3 documents and 10 questions as Phase 3, but retrieval is TF-IDF (no embedding model):

Corpus: ~42 chunks from hr_policy_th.md, tech_docs_en.md, faq_mixed.md

Test questions: 10 questions across Thai HR, English API, English Security, Thai Mixed

### Query Result Structure (Phase 3.5)

```json
{
  "id": 1,
  "question": "...",
  "category": "thai_hr",
  "expected": "10 วันต่อปี",
  "generated": "[LLM-generated answer]",
  "f1_score": 0.85,
  "latency_ms": 450.2,
  "input_tokens": 215,
  "output_tokens": 42,
  "cost_usd": 0.001234
}
```

### Provider Registry

11 provider/model combinations:

| Name | Provider | Model | Cost Input | Cost Output | Lock-in |
|------|----------|-------|-----------|------------|---------|
| openrouter_gpt4o_mini | OpenRouter | openai/gpt-4o-mini | $0.15/M | $0.60/M | 3 |
| openrouter_gpt4o | OpenRouter | openai/gpt-4o | $2.50/M | $10.00/M | 3 |
| openrouter_claude_sonnet | OpenRouter | anthropic/claude-3.5-sonnet | $3.00/M | $15.00/M | 3 |
| openrouter_llama3 | OpenRouter | meta-llama/llama-3.1-70b | $0.35/M | $0.40/M | 0 |
| openrouter_gemini_flash | OpenRouter | google/gemini-flash-1.5 | $0.075/M | $0.30/M | 2 |
| openrouter_deepseek | OpenRouter | deepseek/deepseek-chat | $0.14/M | $0.28/M | 1 |
| openai_gpt4o_mini | OpenAI Direct | gpt-4o-mini | $0.15/M | $0.60/M | 8 |
| openai_gpt4o | OpenAI Direct | gpt-4o | $2.50/M | $10.00/M | 8 |
| anthropic_sonnet | Anthropic Direct | claude-3-5-sonnet-20241022 | $3.00/M | $15.00/M | 7 |
| anthropic_haiku | Anthropic Direct | claude-3-haiku-20240307 | $0.80/M | $4.00/M | 7 |
| ollama | Ollama (self-hosted) | llama3.1:8b (default) | $0.0 | $0.0 | 0 |

Default: `openrouter_gpt4o_mini` (fast + cheap)

### Output — `benchmarks/llm-provider/results/llm_provider_results.json`

```json
{
  "phase": "3.5",
  "top_k": 3,
  "chunk_size": 500,
  "chunk_overlap": 50,
  "num_chunks": 42,
  "num_questions": 10,
  "weights": {
    "overall_quality": 0.20,
    "lock_in": 0.20,
    "cost": 0.15,
    "latency": 0.15,
    "thai_quality": 0.10,
    "reliability": 0.10,
    "privacy": 0.05,
    "ease_switching": 0.05
  },
  "results": [
    {
      "provider": "openrouter_gpt4o_mini",
      "meta": { ... },
      "overall_f1": 0.8234,
      "thai_f1": 0.9100,
      "avg_latency_ms": 450.2,
      "total_cost_usd": 0.012450,
      "num_questions": 10,
      "weighted_score": 0.8450,
      "queries": [...]
    }
  ]
}
```

**Ranking:** Results sorted by `weighted_score` (highest first); rank 1 = "⭐ RECOMMENDED"
