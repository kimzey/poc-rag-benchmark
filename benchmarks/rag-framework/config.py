"""Shared configuration for Phase 2 RAG Framework benchmark."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── LLM via OpenRouter ────────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
LLM_MODEL: str = os.getenv("RAG_LLM_MODEL", "anthropic/claude-3-haiku")

# ── Embedding ─────────────────────────────────────────────────────────────────
# Local (sentence-transformers, no key needed):
#   all-MiniLM-L6-v2              → fast, English-focused (~80MB)
#   intfloat/multilingual-e5-small → Thai+English (~470MB)
# OpenAI API (requires OPENAI_API_KEY):
#   text-embedding-3-small        → 1536 dims, $0.02/1M tokens
#   text-embedding-3-large        → 3072 dims, $0.13/1M tokens
EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

# ── Paths ─────────────────────────────────────────────────────────────────────
BENCHMARK_DIR: Path = Path(__file__).parent
DATASETS_DIR: Path = BENCHMARK_DIR.parent.parent / "datasets"
RESULTS_DIR: Path = BENCHMARK_DIR / "results"
