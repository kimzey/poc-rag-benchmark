"""mxbai-embed-large-v1 adapter (mixedbread.ai, open-source, self-hosted)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseEmbeddingModel, ModelMeta


class MxbaiEmbedLargeModel(BaseEmbeddingModel):
    """mixedbread-ai/mxbai-embed-large-v1 — strong English/multilingual, Apache 2.0."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="mxbai-embed-large-v1",
            dimensions=1024,
            max_tokens=512,
            cost_per_1m_tokens=0.0,
            vendor_lock_in=0,
            self_hostable=True,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=16,
        )
