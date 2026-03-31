.PHONY: help up-db down-db install benchmark-quick benchmark-medium benchmark-all \
        install-rag rag-eval rag-eval-framework rag-eval-no-llm

DOCKER_COMPOSE = docker compose -f docker/docker-compose.vector-db.yml
BENCH_DIR      = benchmarks/vector-db
RAG_BENCH_DIR  = benchmarks/rag-framework

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
