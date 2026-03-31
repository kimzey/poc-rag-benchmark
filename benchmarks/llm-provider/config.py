"""Shared configuration for Phase 3.5 LLM Provider benchmark."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY: str     = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str  = os.getenv("ANTHROPIC_API_KEY", "")

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str       = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# ── Generation settings ───────────────────────────────────────────────────────
MAX_NEW_TOKENS: int     = int(os.getenv("LLM_MAX_NEW_TOKENS", "512"))
TEMPERATURE: float      = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# ── Retrieval (keep in sync with Phase 3) ────────────────────────────────────
CHUNK_SIZE: int         = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int      = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
TOP_K: int              = int(os.getenv("RAG_TOP_K", "3"))

# ── Paths ─────────────────────────────────────────────────────────────────────
BENCHMARK_DIR: Path     = Path(__file__).parent
DATASETS_DIR: Path      = BENCHMARK_DIR.parent.parent / "datasets"
RESULTS_DIR: Path       = BENCHMARK_DIR / "results"

# ── RAG system prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY the "
    "information provided in the context below. If the answer is not in the "
    "context, say \"ไม่มีข้อมูลในเอกสาร\" (for Thai) or \"Not found in the "
    "provided context.\" (for English). Be concise."
)

RAG_PROMPT_TEMPLATE = (
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)
