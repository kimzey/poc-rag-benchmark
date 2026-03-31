"""multilingual-e5-large adapter (Microsoft, open-source, self-hosted)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseEmbeddingModel, ModelMeta

# E5 models require the "query: " / "passage: " prefix for best results
_QUERY_PREFIX = "query: "
_PASSAGE_PREFIX = "passage: "


class MultilingualE5LargeModel(BaseEmbeddingModel):
    """intfloat/multilingual-e5-large — Microsoft multilingual, MIT license."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("intfloat/multilingual-e5-large")
        self._is_query = False  # toggled via encode_query / encode_passages

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="multilingual-e5-large",
            dimensions=1024,
            max_tokens=512,
            cost_per_1m_tokens=0.0,
            vendor_lock_in=0,
            self_hostable=True,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        # Prefix is part of the model's training protocol
        prefixed = [
            (_QUERY_PREFIX if self._is_query else _PASSAGE_PREFIX) + t
            for t in texts
        ]
        return self._model.encode(
            prefixed,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=16,
        )

    # ── Override encode to handle query vs passage prefix ────────────────────

    def encode_queries(self, texts: list[str]):
        """Encode queries with 'query: ' prefix."""
        from base import EmbedResult
        import time
        self._is_query = True
        t0 = time.perf_counter()
        raw = self._encode_raw(texts)
        self._is_query = False
        return EmbedResult(embeddings=raw.astype("float32"), latency_ms=(time.perf_counter() - t0) * 1000)

    def encode_passages(self, texts: list[str]):
        """Encode passages with 'passage: ' prefix."""
        from base import EmbedResult
        import time
        self._is_query = False
        t0 = time.perf_counter()
        raw = self._encode_raw(texts)
        return EmbedResult(embeddings=raw.astype("float32"), latency_ms=(time.perf_counter() - t0) * 1000)
