.PHONY: help setup up-db down-db \
        install install-rag install-embed install-llm install-api install-test install-tui \
        benchmark-quick benchmark-medium benchmark-all benchmark-db \
        rag-eval rag-eval-framework rag-eval-no-llm \
        embed-eval embed-eval-all embed-eval-model embed-eval-topk \
        llm-eval llm-eval-all llm-eval-provider llm-eval-topk \
        api-run api-demo \
        test-integration test-integration-verbose load-test \
        tui tui-embedded \
        logs-db ps-db

API_DIR         = api
TEST_DIR        = tests
DOCKER_COMPOSE  = docker compose -f docker/docker-compose.vector-db.yml
BENCH_DIR       = benchmarks/vector-db
RAG_BENCH_DIR   = benchmarks/rag-framework
EMBED_BENCH_DIR = benchmarks/embedding-model
LLM_BENCH_DIR   = benchmarks/llm-provider

# uv — fast Python package manager (https://docs.astral.sh/uv)
UV = uv

help:
	@echo ""
	@echo "  Setup"
	@echo "  ─────"
	@echo "  make setup              Check uv is installed + print quick-start"
	@echo ""
	@echo "  Phase 1 — Vector DB Spike"
	@echo "  ─────────────────────────"
	@echo "  make up-db              Start all Vector DBs (Docker)"
	@echo "  make up-db DB=qdrant    Start single DB (qdrant|pgvector|milvus|opensearch)"
	@echo "  make down-db            Stop & remove all DB containers + volumes"
	@echo "  make install            Install deps for Phase 1  (bench-vectordb group)"
	@echo "  make benchmark-quick    Run benchmark: 10K vectors"
	@echo "  make benchmark-medium   Run benchmark: 100K vectors"
	@echo "  make benchmark-all      Run benchmark: 10K + 100K vectors"
	@echo ""
	@echo "  Phase 2 — RAG Framework Comparison"
	@echo "  ────────────────────────────────────"
	@echo "  make install-rag                Install deps for Phase 2  (bench-rag group, ~2GB)"
	@echo "  make rag-eval                   Run all 4 frameworks (requires OPENROUTER_API_KEY)"
	@echo "  make rag-eval-no-llm            Run indexing only (no API key needed)"
	@echo "  make rag-eval-framework F=name  Run single framework (bare_metal|llamaindex|langchain|haystack)"
	@echo ""
	@echo "  Phase 3 — Embedding Model Comparison"
	@echo "  ──────────────────────────────────────"
	@echo "  make install-embed              Install deps for Phase 3  (bench-embed group)"
	@echo "  make embed-eval                 Run open-source models (no API key needed)"
	@echo "  make embed-eval-all             Run all models (requires OPENAI_API_KEY)"
	@echo "  make embed-eval-model M=name    Run single model"
	@echo "  make embed-eval-topk K=5        Override top-k (default: 3)"
	@echo ""
	@echo "  Phase 3.5 — LLM Provider Comparison"
	@echo "  ──────────────────────────────────────"
	@echo "  make install-llm                Install deps for Phase 3.5  (bench-llm group)"
	@echo "  make llm-eval                   Run default provider (openrouter gpt-4o-mini)"
	@echo "  make llm-eval-all               Run all configured providers"
	@echo "  make llm-eval-provider P=name   Run single provider"
	@echo ""
	@echo "  Phase 4 — API Layer & Auth Design"
	@echo "  ───────────────────────────────────"
	@echo "  make install-api            Install deps for Phase 4  (api group)"
	@echo "  make api-run                Start FastAPI server (http://localhost:8000/docs)"
	@echo "  make api-demo               Quick smoke test (no API key needed)"
	@echo ""
	@echo "  Phase 5 — Integration Testing"
	@echo "  ──────────────────────────────"
	@echo "  make install-test                Install deps for Phase 5  (test group)"
	@echo "  make test-integration            Run all 7 E2E integration test scenarios"
	@echo "  make test-integration-verbose    Run with full output (no capture)"
	@echo "  make load-test                   Locust load test (requires: make api-run)"
	@echo ""
	@echo "  Load test options: make load-test U=100 R=10 T=60s"
	@echo ""
	@echo "  Phase 6 — TUI (Terminal User Interface)"
	@echo "  ────────────────────────────────────────"
	@echo "  make install-tui            Install TUI deps (textual + api group)"
	@echo "  make tui                    Launch TUI (requires: make api-run)"
	@echo "  make tui-embedded           Launch TUI in embedded mode (no server needed)"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────

setup:
	@echo "\n=== spike-rak setup check ===\n"
	@$(UV) --version || (echo "ERROR: uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	@echo "✓ uv found"
	@test -f .env || (cp .env.example .env && echo "✓ Created .env from .env.example (fill in API keys)")
	@echo "\nQuick start:"
	@echo "  API server:        make install-api && make api-run"
	@echo "  Integration tests: make install-test && make test-integration"
	@echo "  Vector DB bench:   make up-db && make install && make benchmark-quick"
	@echo ""

# ── Phase 1: Vector DB ────────────────────────────────────────────────────────

up-db:
ifdef DB
	$(DOCKER_COMPOSE) up -d $(DB)
else
	$(DOCKER_COMPOSE) up -d
endif

down-db:
	$(DOCKER_COMPOSE) down -v

install:
	$(UV) sync --group bench-vectordb

benchmark-quick:
	$(UV) run python $(BENCH_DIR)/run_benchmark.py --n 10000

benchmark-medium:
	$(UV) run python $(BENCH_DIR)/run_benchmark.py --n 100000

benchmark-all: benchmark-quick benchmark-medium

benchmark-db:
	$(UV) run python $(BENCH_DIR)/run_benchmark.py --db $(DB) --n $(or $(N),10000)

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
	$(UV) sync --group bench-rag

rag-eval:
	$(UV) run python $(RAG_BENCH_DIR)/evaluate.py --frameworks all

rag-eval-no-llm:
	$(UV) run python $(RAG_BENCH_DIR)/evaluate.py --frameworks all --no-llm

rag-eval-framework:
	$(UV) run python $(RAG_BENCH_DIR)/evaluate.py --frameworks $(F)

# ── Phase 3: Embedding Model ──────────────────────────────────────────────────

install-embed:
	$(UV) sync --group bench-embed

embed-eval:
	$(UV) run python $(EMBED_BENCH_DIR)/evaluate.py

embed-eval-all:
	$(UV) run python $(EMBED_BENCH_DIR)/evaluate.py --models all

embed-eval-model:
	$(UV) run python $(EMBED_BENCH_DIR)/evaluate.py --models $(M)

embed-eval-topk:
	$(UV) run python $(EMBED_BENCH_DIR)/evaluate.py --top-k $(or $(K),5)

# ── Phase 3.5: LLM Provider ───────────────────────────────────────────────────

install-llm:
	$(UV) sync --group bench-llm

llm-eval:
	$(UV) run python $(LLM_BENCH_DIR)/evaluate.py

llm-eval-all:
	$(UV) run python $(LLM_BENCH_DIR)/evaluate.py --providers all

llm-eval-provider:
	$(UV) run python $(LLM_BENCH_DIR)/evaluate.py --providers $(P)

llm-eval-topk:
	$(UV) run python $(LLM_BENCH_DIR)/evaluate.py --top-k $(or $(K),5)

# ── Phase 4: API Layer & Auth ─────────────────────────────────────────────────

install-api:
	$(UV) sync --group api

api-run:
	$(UV) run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

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
	$(UV) sync --group test

test-integration:
	$(UV) run pytest $(TEST_DIR)/integration/ -v --tb=short -s

test-integration-verbose:
	$(UV) run pytest $(TEST_DIR)/integration/ -v --tb=long -s --no-header

load-test:
	@echo "\n=== Phase 5 Load Test (Locust headless) ===\n"
	@echo "Requires: make api-run in another terminal"
	$(UV) run locust -f $(TEST_DIR)/load/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		--users $(or $(U),50) \
		--spawn-rate $(or $(R),5) \
		--run-time $(or $(T),30s) \
		--only-summary

# ── Phase 6: TUI (Terminal User Interface) ────────────────────────────────────

TUI_DIR = tui

install-tui:
	$(UV) sync --group tui

tui:
	$(UV) run python -m tui

tui-embedded:
	TUI_EMBEDDED_MODE=true $(UV) run python -m tui
