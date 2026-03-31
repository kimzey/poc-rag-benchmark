"""BGE-M3 embedding model adapter (BAAI/bge-m3, open-source, self-hosted)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseEmbeddingModel, ModelMeta


class BGEM3Model(BaseEmbeddingModel):
    """BAAI/bge-m3 — strong multilingual model, runs locally via sentence-transformers."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("BAAI/bge-m3")

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="BGE-M3",
            dimensions=1024,
            max_tokens=8192,
            cost_per_1m_tokens=0.0,   # self-hosted, no API cost
            vendor_lock_in=0,          # fully open-source (Apache 2.0)
            self_hostable=True,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32,
        )
