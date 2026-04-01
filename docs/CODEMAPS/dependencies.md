<!-- Generated: 2026-04-01 | Files scanned: 5 | Token estimate: ~600 -->

# Dependencies & External Services Codemap

**Last Updated:** 2026-04-01 (Stable since Phase 6 completed)  
**Tool:** uv (Python 3.11+), Docker Compose, Makefile

## Dependency Groups (uv)

**Installation via:** `uv sync --group <name>` or `make install-<name>`

### Phase 1: Vector DB Benchmark

**Group:** `bench-vectordb` (~500MB)

```toml
qdrant-client>=1.9.0          # Qdrant vector DB client
psycopg2-binary>=2.9.9        # PostgreSQL driver (for pgvector)
pgvector>=0.2.5               # pgvector Python bindings
pymilvus>=2.4.0               # Milvus vector DB client
opensearch-py>=2.5.0          # OpenSearch client
numpy>=1.26.0                 # Numerical arrays
tqdm>=4.66.0                  # Progress bars
rich>=13.7.0                  # Colored output
python-dotenv>=1.0.0          # .env file loading
```

### Phase 2: RAG Framework Benchmark

**Group:** `bench-rag` (~2GB, heaviest phase)

```toml
openai>=1.30.0                # OpenRouter (OpenAI-compatible)
sentence-transformers>=3.0.0  # Embedding model library
torch>=2.0.0                  # PyTorch (for transformers)
llama-index-core>=0.11.0      # LlamaIndex framework
llama-index-llms-openai>=0.3.0
llama-index-embeddings-huggingface>=0.3.0
llama-index-embeddings-openai>=0.3.0
langchain>=0.3.0              # LangChain framework
langchain-community>=0.3.0
langchain-openai>=0.2.0
langchain-huggingface>=0.1.0
faiss-cpu>=1.8.0              # FAISS vector similarity (for LangChain)
haystack-ai>=2.5.0            # Haystack framework
python-dotenv>=1.0.0
numpy>=1.26.0
rich>=13.7.0
tqdm>=4.66.0
```

### Phase 3: Embedding Model Benchmark

**Group:** `bench-embed` (~2GB)

```toml
sentence-transformers>=3.0.0  # HuggingFace embedding models
torch>=2.0.0                  # PyTorch (for transformers)
openai>=1.30.0                # OpenAI embeddings API
python-dotenv>=1.0.0
numpy>=1.26.0
rich>=13.7.0
transformers>=4.40.0          # HuggingFace transformers
cohere>=5.0                   # Cohere API client
sentencepiece>=0.2.0          # Tokenizer (for multilingual models)
```

### Phase 3.5: LLM Provider Benchmark

**Group:** `bench-llm` (~100MB)

```toml
openai>=1.30.0                # OpenRouter (OpenAI-compatible) + OpenAI direct
anthropic>=0.28.0             # Anthropic Claude API
python-dotenv>=1.0.0
rich>=13.7.0
```

### Phase 4: API Server

**Group:** `api` (~300MB)

```toml
fastapi==0.115.12             # Web framework
uvicorn[standard]==0.34.0     # ASGI server
pydantic==2.11.3              # Data validation
pydantic-settings==2.8.1      # Settings from .env
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4        # Password hashing
bcrypt==4.0.1                 # Bcrypt hashing algorithm
openai==1.71.0                # OpenRouter (OpenAI-compatible)
httpx==0.28.1                 # Async HTTP client
python-multipart==0.0.20      # Form/file upload parsing
```

### Phase 5: Integration Tests

**Group:** `test` (~400MB, includes `api`)

```toml
{ include-group = "api" }      # Includes all API dependencies
pytest==8.3.5                 # Testing framework
pytest-asyncio==0.25.3        # Async test support
locust==2.32.4                # Load testing framework
```

### Phase 6: Terminal User Interface

**Group:** `tui` (~50MB, includes `api`)

```toml
{ include-group = "api" }      # Includes all API dependencies
textual>=0.80.0               # Textual TUI framework
```

## Docker Services (Vector DBs)

**File:** `docker/docker-compose.vector-db.yml`

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"           # HTTP API
    volumes:
      - qdrant_storage:/qdrant/storage

  postgres:
    image: postgres:15
    ports:
      - "5433:5432"           # pgvector runs on standard postgres
    environment:
      POSTGRES_DB: vector_db
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  milvus:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"         # gRPC API
      - "9091:9091"           # Metrics
    volumes:
      - milvus_data:/var/lib/milvus

  opensearch:
    image: opensearchproject/opensearch:latest
    ports:
      - "9200:9200"           # HTTP API
    environment:
      OPENSEARCH_JAVA_OPTS: "-Xms512m -Xmx512m"
      discovery.type: single-node
    volumes:
      - opensearch_data:/usr/share/opensearch/data

volumes:
  qdrant_storage:
  postgres_data:
  milvus_data:
  opensearch_data:
```

**Commands:**

```bash
docker-compose -f docker/docker-compose.vector-db.yml up -d       # Start all
docker-compose -f docker/docker-compose.vector-db.yml down        # Stop all
docker-compose -f docker/docker-compose.vector-db.yml logs -f     # Stream logs
```

Or via Makefile: `make up-db`, `make down-db`, `make logs-db`

## External API Services

### OpenRouter (OpenAI-Compatible LLM Endpoint)

**Used By:** Phase 2, 3.5, Phase 4 API RAG pipeline

**Endpoint:** `https://openrouter.ai/api/v1`

**Models Available:**
- `anthropic/claude-3.5-sonnet` (default in Phase 4)
- `openai/gpt-4-turbo`
- `google/gemini-pro`
- `meta-llama/llama3.1-405b`
- `deepseek/deepseek-chat`
- ... and many others

**Environment Variables:**
```
OPENROUTER_API_KEY=<your-key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1  (default in code)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet      (default)
```

**Setup:**
1. Sign up at https://openrouter.ai
2. Create API key at https://openrouter.ai/keys
3. Add to `.env`: `OPENROUTER_API_KEY=sk-...`
4. Copy `.env.example` as starting point: `cp .env.example .env`

### OpenAI Direct (for embedding models)

**Used By:** Phase 3 embedding benchmark, Phase 4 (optionally)

**Endpoint:** `https://api.openai.com/v1`

**Models:**
- `text-embedding-3-small` (1536 dims, $0.02/1M)
- `text-embedding-3-large` (3072 dims, $0.13/1M)

**Environment Variables:**
```
OPENAI_API_KEY=sk-...
```

### Anthropic Claude Direct (for LLM provider benchmark)

**Used By:** Phase 3.5 LLM provider comparison

**Endpoint:** https://api.anthropic.com/v1

**Models:**
- `claude-3.5-sonnet`
- `claude-3-haiku`

**Environment Variables:**
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Cohere (for embedding model benchmark)

**Used By:** Phase 3 embedding model evaluation

**Endpoint:** https://api.cohere.ai/v1

**Models:**
- `embed-multilingual-v3.0` (1024 dims, $0.10/1M)

**Environment Variables:**
```
COHERE_API_KEY=<your-key>
```

### Ollama (Local LLM Server, Optional)

**Used By:** Phase 3.5 LLM provider benchmark (self-hosted)

**Endpoint:** http://localhost:11434 (default)

**Setup:**
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1:8b
ollama serve  # Starts server on port 11434
```

**Environment Variables:**
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## Python Version & Environment

**Requirements:**
- Python ≥ 3.11
- uv (Python package manager)

**Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: pip install uv
```

**Manage venv:**
```bash
uv sync                    # Install all groups
uv sync --group bench-vectordb   # Phase 1 only
uv sync --group api        # Phase 4 (for API development)
uv run <command>           # Run command in venv (no activation needed)
```

## Configuration Files

### .env (Runtime Configuration)

```bash
# API
OPENROUTER_API_KEY=sk-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# OpenAI (embedding models)
OPENAI_API_KEY=sk-...

# Anthropic (LLM provider comparison)
ANTHROPIC_API_KEY=sk-ant-...

# Cohere (embedding model comparison)
COHERE_API_KEY=...

# Ollama (optional, self-hosted)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# TUI
API_BASE_URL=http://localhost:8000
```

**Get template:** `cp .env.example .env`

### pyproject.toml (Dependency Management)

- Defines all dependency groups (Phases 1-6)
- Marker: `[dependency-groups]`
- Each group: `<name> = [...]`

### docker-compose.vector-db.yml (Container Orchestration)

- 4 vector DB services (Qdrant, pgvector, Milvus, OpenSearch)
- Each with exposed ports, volumes, environment variables
- Usage: `docker-compose -f docker/docker-compose.vector-db.yml up -d`

## Makefile Commands

**Install Phase Groups:**
```bash
make setup               # Check prereqs, create .env
make install             # Phase 1: vector-db benchmarks
make install-rag         # Phase 2: RAG frameworks
make install-embed       # Phase 3: embedding models
make install-llm         # Phase 3.5: LLM providers
make install-api         # Phase 4: FastAPI server
make install-test        # Phase 5: integration tests (includes api)
```

**Run & Test:**
```bash
make up-db               # Start Docker services (vector DBs)
make down-db             # Stop Docker services
make api-run             # Start FastAPI server (http://localhost:8000)
make tui                 # Start Textual TUI
make test-integration    # Run all 27 integration tests
make rag-eval            # Evaluate Phase 2 frameworks
make embed-eval          # Evaluate Phase 3 embedding models
make llm-eval            # Evaluate Phase 3.5 LLM providers
```

## Related Codemaps

- **[architecture.md](architecture.md)** — Overall system using these dependencies
- **[backend.md](backend.md)** — API server (uses `api` group + OpenRouter)
- **[tui.md](tui.md)** — TUI app (uses `tui` group + API)
- **[benchmarks.md](benchmarks.md)** — Benchmark phases using respective groups
