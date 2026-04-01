<!-- Generated: 2026-04-01 | Files scanned: 20 | Token estimate: ~750 -->

# Benchmarks Codemap

**Last Updated:** 2026-04-01  
**Phases:** 1, 2, 3, 3.5 (all benchmarking modules)  
**Design Pattern:** ABC base class + pluggable implementations

## Phase 1: Vector DB Benchmark

**File:** `benchmarks/vector-db/`

### VectorDBClient ABC (`clients/base.py`)

```python
class VectorDBClient(ABC):
    """Uniform interface for all 4 Vector DB implementations."""
    DIM = 1536  # Match OpenAI text-embedding-3-small

    @abstractmethod
    def connect() → None
    @abstractmethod
    def create_collection(name: str) → None
    @abstractmethod
    def insert(records: list[BenchmarkRecord]) → None
    @abstractmethod
    def search(
        query_vector: list[float],
        top_k: int = 10,
        filter: dict | None = None
    ) → list[SearchResult]
    @abstractmethod
    def count() → int
    @abstractmethod
    def drop_collection() → None
    @property
    @abstractmethod
    def name() → str

@dataclass
class SearchResult:
    id: str
    score: float
    metadata: dict

@dataclass
class BenchmarkRecord:
    id: str
    vector: list[float]
    metadata: dict  # access_level, category, source
```

### Implementations

| Implementation | Location | Deps | Metadata Filter |
|---|---|---|---|
| **Qdrant** | `qdrant/client.py` | qdrant-client | Filter(must=[...]) |
| **pgvector** | `pgvector/client.py` | psycopg2, pgvector | WHERE metadata->'access_level' |
| **Milvus** | `milvus/client.py` | pymilvus | expr="access_level == ..." |
| **OpenSearch** | `opensearch/client.py` | opensearch-py | query bool filter |

### Benchmark Runner (`run_benchmark.py`)

```python
# Usage: uv run benchmarks/vector-db/run_benchmark.py --vdb qdrant --dim 1536 --vectors 10000
# Outputs: latency p50/p95/p99, QPS, recall@10 for each DB

def generate_dataset(n: int) → list[BenchmarkRecord]:
    # Random 1536-dim unit vectors

for db_name in CLIENTS_MAP:
    client = CLIENTS_MAP[db_name]()
    client.connect()
    client.create_collection("benchmark")
    
    # Insert latency
    t0 = time.perf_counter()
    client.insert(dataset)
    insert_time = (time.perf_counter() - t0) * 1000
    
    # Search latency (100 queries)
    for _ in range(100):
        t0 = time.perf_counter()
        results = client.search(query_vector, top_k=10, filter=access_level_filter)
        search_latencies.append((time.perf_counter() - t0) * 1000)
    
    print_stats(p50, p95, p99, QPS, recall@10)
```

## Phase 2: RAG Framework Benchmark

**File:** `benchmarks/rag-framework/`

### BaseRAGPipeline ABC (`base.py`)

```python
@dataclass
class RAGResult:
    answer: str
    sources: list[str]
    latency_ms: float
    retrieved_chunks: list[str]

@dataclass
class IndexStats:
    num_chunks: int
    indexing_time_ms: float
    framework: str

class BaseRAGPipeline(ABC):
    """Common interface for 4 RAG frameworks."""

    @property
    @abstractmethod
    def name() → str:  # "bare_metal", "llamaindex", "langchain", "haystack"

    @abstractmethod
    def build_index(doc_paths: list[str]) → IndexStats:
        """Load, chunk, embed (sentence-transformers), store in-memory."""

    @abstractmethod
    def query(question: str, top_k: int = 3) → RAGResult:
        """Embed query → cosine retrieve → LLM generate."""

    @property
    def pipeline_file() → Path:
        """Path to pipeline.py (for LOC counting)."""

    @property
    def loc() → int:
        """Non-blank, non-comment line count."""
```

### Implementations

| Framework | Vector Store | Chunker | LLM | LOC |
|---|---|---|---|---|
| **bare_metal** | numpy dot product | word split | openai.AsyncOpenAI(base_url=openrouter) | ~150 |
| **LlamaIndex** | VectorStoreIndex (RAM) | SentenceSplitter | LlamaOpenAI(api_base=openrouter) | ~100 |
| **LangChain** | FAISS (RAM) | RecursiveCharacterTextSplitter | ChatOpenAI(openai_api_base=openrouter) | ~120 |
| **Haystack** | InMemoryDocumentStore | word split | OpenAIGenerator(api_base_url=openrouter) | ~140 |

### Evaluator (`evaluate.py`)

```python
# Usage: make rag-eval  (requires OPENROUTER_API_KEY)
# Compares: latency, indexing time, LOC, component swap-ability

for framework_name, FrameworkClass in FRAMEWORK_REGISTRY.items():
    pipeline = FrameworkClass()

    # Index 3 sample docs (Thai HR + English Tech + Mixed FAQ)
    index_stats = pipeline.build_index([
        "datasets/thai_hr_policy.md",
        "datasets/english_tech.md",
        "datasets/mixed_faq.md",
    ])

    # Query 10 questions
    for question in QUESTIONS:
        t0 = time.perf_counter()
        result = pipeline.query(question, top_k=3)
        latency_ms = (time.perf_counter() - t0) * 1000

    # Print comparison table
    print_comparison_table(
        ["Framework", "Indexing (ms)", "Query Latency (ms)", "LOC", "Components"],
        results,
    )
```

## Phase 3: Embedding Model Benchmark

**File:** `benchmarks/embedding-model/`

### BaseEmbeddingModel ABC (`base.py`)

```python
@dataclass
class EmbedResult:
    embeddings: np.ndarray  # shape (n, dims), L2-normalized
    latency_ms: float

@dataclass
class ModelMeta:
    name: str
    dimensions: int
    max_tokens: int
    cost_per_1m_tokens: float  # USD; 0.0 for open-source
    vendor_lock_in: int        # 0 = fully open, 10 = hard lock-in
    self_hostable: bool

class BaseEmbeddingModel(ABC):
    """Common interface for embedding models."""

    @property
    @abstractmethod
    def meta() → ModelMeta

    @abstractmethod
    def _encode_raw(texts: list[str]) → np.ndarray:
        """Encode → shape (n, dims), may or may not be normalized."""

    def encode(texts: list[str]) → EmbedResult:
        """Public API: encode + L2-normalize + track latency."""
```

### Implementations

| Model | Location | Type | Dims | Max Tokens | Cost |
|---|---|---|---|---|---|
| **BGE-M3** | `bge_m3/model.py` | Open (HF) | 1024 | 8192 | $0.00 |
| **E5 Multilingual** | `multilingual_e5/model.py` | Open (HF) | 1024 | 512 | $0.00 |
| **MxBai Embed** | `mxbai/model.py` | Open (HF) | 1024 | 512 | $0.00 |
| **WangchanBERTa** | `wangchanberta/model.py` | Open (HF, Thai-optimized) | 768 | 512 | $0.00 |
| **OpenAI 3-small** | `openai/model.py` | Commercial | 1536 | 8191 | $0.02/1M |
| **OpenAI 3-large** | `openai/model.py` | Commercial | 3072 | 8191 | $0.13/1M |
| **Cohere V3** | `cohere/model.py` | Commercial | 1024 | 512 | $0.10/1M |

### Evaluator (`evaluate.py`)

```python
# Usage: make embed-eval  (requires API keys for paid models)
# Measures: recall@k, MRR, latency, cost, weighted scorecard

for model_name, ModelClass in MODEL_REGISTRY.items():
    model = ModelClass()
    
    # Encode corpus (Thai + English docs)
    corpus_embeds = model.encode(corpus_texts)  # → (n, dims)
    
    # For each question:
    for question in QUESTIONS:
        query_embed = model.encode([question])[0]
        scores = corpus_embeds @ query_embed  # cosine similarity
        top_k_ids = argsort(scores)[-top_k:]
        
        # Check if ground-truth chunk in top-k
        recall@k = 1 if gt_chunk_id in top_k_ids else 0
        mrr = 1 / (rank_of_gt_chunk + 1)
    
    # Compute weighted scorecard:
    # 25% Thai · 15% English · 15% Latency · 15% Cost · 10% Self-host · 5% Dims · 5% MaxTok · 10% Lock-in
    
print_rankings(models_by_weighted_score)
print_json_export("results/embedding_models.json", rankings)
```

## Phase 3.5: LLM Provider Benchmark

**File:** `benchmarks/llm-provider/`

### BaseLLMProvider ABC (`base.py`)

```python
@dataclass
class GenerateResult:
    text: str               # Generated answer text
    latency_ms: float       # Wall time for full response
    input_tokens: int
    output_tokens: int
    cost_usd: float         # Estimated cost for this call

@dataclass
class ProviderMeta:
    name: str               # e.g. "OpenRouter / claude-3.5-sonnet"
    model_id: str           # API model identifier
    provider: str           # "openrouter" | "openai" | "anthropic" | "ollama"
    cost_per_1m_input: float
    cost_per_1m_output: float
    vendor_lock_in: int     # 0 = open, 10 = proprietary
    self_hostable: bool
    openai_compatible: bool # True if uses OpenAI-compatible API

class BaseLLMProvider(ABC):
    """Common interface for LLM providers."""

    @property
    @abstractmethod
    def meta() → ProviderMeta

    @abstractmethod
    def _generate_raw(prompt: str, context: str) → tuple[str, int, int]:
        """Send prompt+context, return (answer, input_tokens, output_tokens)."""

    def generate(prompt: str, context: str) → GenerateResult:
        """Public API: wraps _generate_raw(), calculates cost + latency."""
```

### Implementations

| Provider | Location | Models | OpenAI Compatible | Cost |
|---|---|---|---|---|
| **OpenRouter** | `openrouter/provider.py` | 6 models (GPT-4o, Claude 3.5, Gemini, Llama, DeepSeek) | Yes | Variable |
| **OpenAI Direct** | `openai/provider.py` | gpt-4o, gpt-4o-mini | Yes | $0.03-$0.03 input, $0.06-$0.06 output per 1M |
| **Anthropic Direct** | `anthropic/provider.py` | claude-3.5-sonnet, claude-3-haiku | No (native SDK) | $0.80-$3.00 input, $2.40-$15.00 output per 1M |
| **Ollama** | `ollama/provider.py` | llama3.1:8b (self-hosted) | Yes | $0.00 |

### Evaluator (`evaluate.py`)

```python
# Usage: make llm-eval  (requires OPENROUTER_API_KEY + optional others)
# Measures: answer quality (F1), latency, cost, weighted scorecard

for provider_name, ProviderClass in PROVIDER_REGISTRY.items():
    provider = ProviderClass()
    
    # For each (question, ground_truth_answer):
    for question, expected_answer in QA_PAIRS:
        context = retrieve_tf_idf(question, corpus)
        
        result = provider.generate(
            prompt=build_prompt(question),
            context=context,
        )
        
        # Compute answer quality (token F1)
        f1 = token_f1(result.text, expected_answer)
        
        # Track latency + cost
        latencies.append(result.latency_ms)
        total_cost += result.cost_usd
    
    # Weighted scorecard:
    # 20% Quality · 20% Lock-in · 15% Cost · 15% Latency · 10% Thai · 10% Reliability · 5% Privacy · 5% Ease-of-switch
    
print_rankings(providers_by_weighted_score)
print_json_export("results/llm_providers.json", rankings)
```

## Extending Benchmarks

### Add New Vector DB (Phase 1)

1. Create `benchmarks/vector-db/mynewdb/client.py`
2. Inherit `VectorDBClient` and implement 6 methods
3. Add to `CLIENTS_MAP` in `run_benchmark.py`
4. Add Docker service to `docker/docker-compose.vector-db.yml`

### Add New RAG Framework (Phase 2)

1. Create `benchmarks/rag-framework/frameworks/myfw/pipeline.py`
2. Inherit `BaseRAGPipeline` and implement 2 methods
3. Add to `FRAMEWORK_REGISTRY` in `evaluate.py`

### Add New Embedding Model (Phase 3)

1. Create `benchmarks/embedding-model/mymodel/model.py`
2. Inherit `BaseEmbeddingModel` and implement `_encode_raw()` + `meta`
3. Add to `MODEL_REGISTRY` in `evaluate.py`

### Add New LLM Provider (Phase 3.5)

1. Create `benchmarks/llm-provider/myprovider/provider.py`
2. Inherit `BaseLLMProvider` and implement `_generate_raw()` + `meta`
3. Add to `PROVIDER_REGISTRY` in `evaluate.py`
4. Update `.env.example` with required API keys

## Related Codemaps

- **[architecture.md](architecture.md)** — Overall system structure
- **[dependencies.md](dependencies.md)** — Docker services for vector DBs
