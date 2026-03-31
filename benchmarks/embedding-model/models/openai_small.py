"""OpenAI text-embedding-3-small adapter (commercial, requires OPENAI_API_KEY)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseEmbeddingModel, ModelMeta

_BATCH = 100


class OpenAISmallModel(BaseEmbeddingModel):
    """text-embedding-3-small — 1536 dims, cost-efficient. $0.02/1M tokens."""

    def __init__(self) -> None:
        if not config.OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY not set — skipping text-embedding-3-small. "
                "Add it to .env to include this model."
            )
        from openai import OpenAI
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="text-embedding-3-small",
            dimensions=1536,
            max_tokens=8191,
            cost_per_1m_tokens=0.02,
            vendor_lock_in=9,
            self_hostable=False,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH):
            batch = texts[i : i + _BATCH]
            resp = self._client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in resp.data])
        return np.array(all_embeddings, dtype=np.float32)
