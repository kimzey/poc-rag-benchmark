.PHONY: help up-db down-db install benchmark-quick benchmark-medium benchmark-all \
        install-rag rag-eval rag-eval-framework rag-eval-no-llm \
        install-embed embed-eval embed-eval-all embed-eval-model \
        install-llm llm-eval llm-eval-all llm-eval-provider \
        install-api api-run api-demo \
        install-test test-integration test-integration-verbose load-test

API_DIR         = api
TEST_DIR        = tests
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
	@echo "  Phase 4 — API Layer & Auth Design"
	@echo "  ───────────────────────────────────"
	@echo "  make install-api            Install Python deps for Phase 4"
	@echo "  make api-run                Start FastAPI server (http://localhost:8000/docs)"
	@echo "  make api-demo               Quick smoke test (no API key needed)"
	@echo ""
	@echo "  Phase 5 — Integration Testing"
	@echo "  ──────────────────────────────"
	@echo "  make install-test                Install Python deps for Phase 5"
	@echo "  make test-integration            Run all 7 E2E integration test scenarios"
	@echo "  make test-integration-verbose    Run with full output (no capture)"
	@echo "  make load-test                   Run Locust load test (requires: make api-run)"
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

# ── Phase 4: API Layer & Auth ─────────────────────────────────────────────────

install-api:
	pip install -r $(API_DIR)/requirements.txt

api-run:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

api-demo:
	@echo "\n=== Phase 4 PoC Smoke Test ===\n"
	@echo "1) Login as employee → get JWT"
	@TOKEN=$$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
		-H "Content-Type: application/json" \
		-d '{"username":"bob_employee","password":"emp123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	echo "   Token: $$TOKEN\n"; \
	echo "2) GET /me — check user info & permissions"; \
	curl -s http://localhost:8000/api/v1/me -H "Authorization: Bearer $$TOKEN" | python3 -m json.tool; \
	echo "\n3) POST /chat/completions — RAG query (permission-filtered)"; \
	curl -s -X POST http://localhost:8000/api/v1/chat/completions \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		-d '{"messages":[{"role":"user","content":"นโยบายการลาพักร้อนเป็นอย่างไร?"}],"top_k":3}' | python3 -m json.tool

# ── Phase 5: Integration Testing ─────────────────────────────────────────────

install-test:
	pip install -r $(API_DIR)/requirements.txt
	pip install -r $(TEST_DIR)/requirements.txt

test-integration:
	pytest $(TEST_DIR)/integration/ -v --tb=short -s

test-integration-verbose:
	pytest $(TEST_DIR)/integration/ -v --tb=long -s --no-header

load-test:
	@echo "\n=== Phase 5 Load Test (Locust headless) ===\n"
	@echo "Make sure 'make api-run' is running in another terminal."
	locust -f $(TEST_DIR)/load/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		--users $(or $(U),50) \
		--spawn-rate $(or $(R),5) \
		--run-time $(or $(T),30s) \
		--only-summary
