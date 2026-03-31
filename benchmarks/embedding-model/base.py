"""Abstract base class for Phase 3 Embedding Model benchmark."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class EmbedResult:
    embeddings: np.ndarray      # shape (n, dims), L2-normalized
    latency_ms: float           # total wall time for this batch


@dataclass
class ModelMeta:
    """Static facts about an embedding model (no API call needed)."""
    name: str
    dimensions: int
    max_tokens: int
    cost_per_1m_tokens: float   # USD; 0.0 for open-source/self-hosted
    vendor_lock_in: int         # 0 = fully open, 10 = hard lock-in
    self_hostable: bool


class BaseEmbeddingModel(ABC):
    """Common interface every embedding model adapter must implement."""

    # ── Identity & metadata ──────────────────────────────────────────────────

    @property
    @abstractmethod
    def meta(self) -> ModelMeta: ...

    # ── Encoding ─────────────────────────────────────────────────────────────

    @abstractmethod
    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        """Encode texts → float32 array of shape (len(texts), dims).
        Implementations may or may not return normalized embeddings;
        the public `encode()` method always normalizes."""
        ...

    def encode(self, texts: list[str]) -> EmbedResult:
        """Encode and L2-normalize. Returns EmbedResult with timing."""
        t0 = time.perf_counter()
        raw = self._encode_raw(texts)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normalized = (raw / norms).astype(np.float32)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return EmbedResult(embeddings=normalized, latency_ms=elapsed_ms)
