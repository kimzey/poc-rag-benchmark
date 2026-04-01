"""Cohere embed-multilingual-v3.0 adapter (commercial, requires COHERE_API_KEY)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseEmbeddingModel, ModelMeta

_BATCH = 96  # Cohere supports up to 96 texts per call


class CohereEmbedV3Model(BaseEmbeddingModel):
    """Cohere embed-multilingual-v3.0 — strong multilingual, 1024 dims. $0.10/1M tokens."""

    def __init__(self) -> None:
        if not config.COHERE_API_KEY:
            raise EnvironmentError(
                "COHERE_API_KEY not set — skipping Cohere embed-v3. "
                "Add it to .env to include this model."
            )
        import cohere
        self._client = cohere.Client(api_key=config.COHERE_API_KEY)

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="Cohere embed-multilingual-v3.0",
            dimensions=1024,
            max_tokens=512,
            cost_per_1m_tokens=0.10,
            vendor_lock_in=7,
            self_hostable=False,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH):
            batch = texts[i : i + _BATCH]
            resp = self._client.embed(
                texts=batch,
                model="embed-multilingual-v3.0",
                input_type="search_document",
            )
            all_embeddings.extend(resp.embeddings)
        return np.array(all_embeddings, dtype=np.float32)

    def encode_queries(self, texts: list[str]):
        """Cohere recommends input_type='search_query' for queries."""
        import time
        t0 = time.perf_counter()

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH):
            batch = texts[i : i + _BATCH]
            resp = self._client.embed(
                texts=batch,
                model="embed-multilingual-v3.0",
                input_type="search_query",
            )
            all_embeddings.extend(resp.embeddings)

        raw = np.array(all_embeddings, dtype=np.float32)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normalized = (raw / norms).astype(np.float32)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        from base import EmbedResult
        return EmbedResult(embeddings=normalized, latency_ms=elapsed_ms)

    def encode_passages(self, texts: list[str]):
        """Use search_document input_type for passages (same as _encode_raw but with timing)."""
        return self.encode(texts)
