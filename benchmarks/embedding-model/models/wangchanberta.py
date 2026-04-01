"""WangchanBERTa embedding adapter (Thai-specific, open-source, self-hosted)."""
from __future__ import annotations

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseEmbeddingModel, ModelMeta


class WangchanBERTaModel(BaseEmbeddingModel):
    """
    WangchanBERTa — Thai-specific transformer by VISTEC-depa.

    Uses mean pooling over token embeddings to produce sentence-level vectors.
    Model: airesearch/wangchanberta-base-att-spm-uncased
    """

    MODEL_ID = "airesearch/wangchanberta-base-att-spm-uncased"

    def __init__(self) -> None:
        from transformers import AutoTokenizer, AutoModel
        self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
        self._model = AutoModel.from_pretrained(self.MODEL_ID)
        self._model.eval()

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="WangchanBERTa",
            dimensions=768,
            max_tokens=416,
            cost_per_1m_tokens=0.0,
            vendor_lock_in=0,
            self_hostable=True,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        import torch

        all_embeddings: list[np.ndarray] = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=416,
                return_tensors="pt",
            )
            with torch.no_grad():
                outputs = self._model(**encoded)
            # Mean pooling over token embeddings (excluding padding)
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            token_embs = outputs.last_hidden_state
            summed = (token_embs * attention_mask).sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1e-9)
            mean_pooled = (summed / counts).numpy()
            all_embeddings.append(mean_pooled)

        return np.concatenate(all_embeddings, axis=0).astype(np.float32)
