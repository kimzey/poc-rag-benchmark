.PHONY: help up-db down-db install benchmark-quick benchmark-medium benchmark-all

DOCKER_COMPOSE = docker compose -f docker/docker-compose.vector-db.yml
BENCH_DIR      = benchmarks/vector-db

help:
	@echo ""
	@echo "  Phase 1 — Vector DB Spike"
	@echo "  ─────────────────────────"
	@echo "  make up-db              Start all Vector DBs"
	@echo "  make up-db DB=qdrant    Start single DB (qdrant|pgvector|milvus|opensearch)"
	@echo "  make down-db            Stop & remove all DB containers + volumes"
	@echo "  make install            Install Python dependencies"
	@echo "  make benchmark-quick    Run benchmark: 10K vectors"
	@echo "  make benchmark-medium   Run benchmark: 100K vectors"
	@echo "  make benchmark-all      Run benchmark: 10K + 100K vectors"
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
