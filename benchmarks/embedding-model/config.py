"""Shared configuration for Phase 3 Embedding Model benchmark."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── API Keys (optional — models skip gracefully if key missing) ───────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")

# ── Chunking (keep same as Phase 2 for fair comparison) ───────────────────────
CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

# ── Paths ─────────────────────────────────────────────────────────────────────
BENCHMARK_DIR: Path = Path(__file__).parent
DATASETS_DIR: Path = BENCHMARK_DIR.parent.parent / "datasets"
RESULTS_DIR: Path = BENCHMARK_DIR / "results"
