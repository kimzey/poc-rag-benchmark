.PHONY: help up-db down-db install benchmark-quick benchmark-medium benchmark-all \
        install-rag rag-eval rag-eval-framework rag-eval-no-llm \
        install-embed embed-eval embed-eval-all embed-eval-model \
        install-llm llm-eval llm-eval-all llm-eval-provider

DOCKER_COMPOSE  = docker compose -f docker/docker-compose.vector-db.yml
BENCH_DIR       = benchmarks/vector-db
RAG_BENCH_DIR   = benchmarks/rag-framework
EMBED_BENCH_DIR = benchmarks/embedding-model
LLM_BENCH_DIR   = benchmarks/llm-provider

help:
	@echo ""
	@echo "  Phase 1 — Vector DB Spike"
	@echo "  ─────────────────────────"
	@echo "  make up-db              Start all Vector DBs"
	@echo "  make up-db DB=qdrant    Start single DB (qdrant|pgvector|milvus|opensearch)"
	@echo "  make down-db            Stop & remove all DB containers + volumes"
	@echo "  make install            Install Python deps for Phase 1"
	@echo "  make benchmark-quick    Run benchmark: 10K vectors"
	@echo "  make benchmark-medium   Run benchmark: 100K vectors"
	@echo "  make benchmark-all      Run benchmark: 10K + 100K vectors"
	@echo ""
	@echo "  Phase 2 — RAG Framework Comparison"
	@echo "  ────────────────────────────────────"
	@echo "  make install-rag                Install Python deps for Phase 2"
	@echo "  make rag-eval                   Run all 4 frameworks (requires OPENROUTER_API_KEY)"
	@echo "  make rag-eval-no-llm            Run indexing only (no API key needed)"
	@echo "  make rag-eval-framework F=name  Run single framework (bare_metal|llamaindex|langchain|haystack)"
	@echo ""
	@echo "  Phase 3 — Embedding Model Comparison"
	@echo "  ──────────────────────────────────────"
	@echo "  make install-embed              Install Python deps for Phase 3"
	@echo "  make embed-eval                 Run open-source models (no API key needed)"
	@echo "  make embed-eval-all             Run all models (requires OPENAI_API_KEY for OpenAI)"
	@echo "  make embed-eval-model M=name    Run single model (bge_m3|multilingual_e5|mxbai|openai_large|openai_small)"
	@echo "  make embed-eval-topk K=5        Override top-k (default: 3)"
	@echo ""
	@echo "  Phase 3.5 — LLM Provider Comparison"
	@echo "  ──────────────────────────────────────"
	@echo "  make install-llm                Install Python deps for Phase 3.5"
	@echo "  make llm-eval                   Run default provider (openrouter gpt-4o-mini)"
	@echo "  make llm-eval-all               Run all configured providers"
	@echo "  make llm-eval-provider P=name   Run single provider"
	@echo "  make llm-eval-topk K=5          Override top-k (default: 3)"
	@echo ""

up-db:
ifdef DB
	$(DOCKER_COMPOSE) up -d $(DB)
else
	$(DOCKER_COMPOSE) up -d
endif

down-db:
	$(DOCKER_COMPOSE) down -v

install:
	pip install -r $(BENCH_DIR)/requirements.txt

benchmark-quick:
	cd $(BENCH_DIR) && python run_benchmark.py --n 10000

benchmark-medium:
	cd $(BENCH_DIR) && python run_benchmark.py --n 100000

benchmark-all: benchmark-quick benchmark-medium

benchmark-db:
	cd $(BENCH_DIR) && python run_benchmark.py --db $(DB) --n $(or $(N),10000)

logs-db:
ifdef DB
	$(DOCKER_COMPOSE) logs -f $(DB)
else
	$(DOCKER_COMPOSE) logs -f
endif

ps-db:
	$(DOCKER_COMPOSE) ps

# ── Phase 2: RAG Framework ────────────────────────────────────────────────────

install-rag:
	pip install -r $(RAG_BENCH_DIR)/requirements.txt

rag-eval:
	cd $(RAG_BENCH_DIR) && python evaluate.py --frameworks all

rag-eval-no-llm:
	cd $(RAG_BENCH_DIR) && python evaluate.py --frameworks all --no-llm

rag-eval-framework:
	cd $(RAG_BENCH_DIR) && python evaluate.py --frameworks $(F)

# ── Phase 3: Embedding Model ──────────────────────────────────────────────────

install-embed:
	pip install -r $(EMBED_BENCH_DIR)/requirements.txt

embed-eval:
	cd $(EMBED_BENCH_DIR) && python evaluate.py

embed-eval-all:
	cd $(EMBED_BENCH_DIR) && python evaluate.py --models all

embed-eval-model:
	cd $(EMBED_BENCH_DIR) && python evaluate.py --models $(M)

embed-eval-topk:
	cd $(EMBED_BENCH_DIR) && python evaluate.py --top-k $(or $(K),5)

# ── Phase 3.5: LLM Provider ───────────────────────────────────────────────────

install-llm:
	pip install -r $(LLM_BENCH_DIR)/requirements.txt

llm-eval:
	cd $(LLM_BENCH_DIR) && python evaluate.py

llm-eval-all:
	cd $(LLM_BENCH_DIR) && python evaluate.py --providers all

llm-eval-provider:
	cd $(LLM_BENCH_DIR) && python evaluate.py --providers $(P)

llm-eval-topk:
	cd $(LLM_BENCH_DIR) && python evaluate.py --top-k $(or $(K),5)
