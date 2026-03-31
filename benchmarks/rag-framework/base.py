"""Abstract base class for all RAG framework implementations."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RAGResult:
    answer: str
    sources: list[str]
    latency_ms: float
    retrieved_chunks: list[str] = field(default_factory=list)


@dataclass
class IndexStats:
    num_chunks: int
    indexing_time_ms: float
    framework: str = ""


class BaseRAGPipeline(ABC):
    """Common interface for all 4 RAG framework implementations."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def build_index(self, doc_paths: list[str]) -> IndexStats:
        """Load, chunk, embed, and store documents. Returns indexing stats."""
        ...

    @abstractmethod
    def query(self, question: str, top_k: int = 3) -> RAGResult:
        """Embed query → retrieve → generate. Returns answer + metadata."""
        ...

    @property
    def pipeline_file(self) -> Path:
        """Path to this framework's pipeline.py (used for LOC counting)."""
        import inspect
        return Path(inspect.getfile(type(self)))

    @property
    def loc(self) -> int:
        """Lines of code in pipeline.py (proxy for framework complexity)."""
        src = self.pipeline_file.read_text(encoding="utf-8")
        return len([l for l in src.splitlines() if l.strip() and not l.strip().startswith("#")])
