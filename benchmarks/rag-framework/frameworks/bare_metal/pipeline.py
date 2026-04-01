"""
Bare Metal RAG — no framework, every step hand-rolled.

Purpose: establish the baseline of how much code is needed
without any abstraction layer.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from openai import OpenAI

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from base import BaseRAGPipeline, IndexStats, RAGResult

_RAG_PROMPT = """\
You are a helpful assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say "ไม่พบข้อมูลในเอกสาร (No information found in documents)."

Context:
{context}

Question: {question}

Answer:"""


def _is_openai_model(model: str) -> bool:
    return model.startswith("text-embedding")


class BareMetalRAGPipeline(BaseRAGPipeline):
    """Direct implementation: numpy cosine sim + OpenRouter LLM.

    Embedding: OpenAI API when RAG_EMBEDDING_MODEL=text-embedding-*, else sentence-transformers.
    """

    def __init__(self) -> None:
        if _is_openai_model(config.EMBEDDING_MODEL):
            self._embedder = None
            self._openai_embed = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
            )
        else:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(config.EMBEDDING_MODEL)
            self._openai_embed = None
        self._llm = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )
        self._chunks: list[str] = []
        self._sources: list[str] = []
        self._embeddings: np.ndarray | None = None

    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._openai_embed is not None:
            resp = self._openai_embed.embeddings.create(
                model=config.EMBEDDING_MODEL, input=texts
            )
            vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            return vecs / np.where(norms == 0, 1, norms)
        return self._embedder.encode(
            texts, show_progress_bar=False, normalize_embeddings=True, batch_size=32
        )

    @property
    def name(self) -> str:
        return "bare_metal"

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks: list[str] = []
        step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
        i = 0
        while i < len(words):
            chunks.append(" ".join(words[i : i + config.CHUNK_SIZE]))
            i += step
        return chunks

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        t0 = time.perf_counter()
        self._chunks = []
        self._sources = []

        for path in doc_paths:
            text = Path(path).read_text(encoding="utf-8")
            chunks = self._chunk_text(text)
            self._chunks.extend(chunks)
            self._sources.extend([str(path)] * len(chunks))

        self._embeddings = self._embed(self._chunks)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexStats(
            num_chunks=len(self._chunks),
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
        t0 = time.perf_counter()

        q_emb = self._embed([question])[0]
        scores = self._embeddings @ q_emb
        top_idx = np.argsort(scores)[::-1][:top_k]

        retrieved = [self._chunks[i] for i in top_idx]
        sources = [self._sources[i] for i in top_idx]

        context = "\n\n---\n\n".join(retrieved)
        prompt = _RAG_PROMPT.format(context=context, question=question)

        response = self._llm.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        answer = response.choices[0].message.content or ""

        return RAGResult(
            answer=answer,
            sources=sources,
            latency_ms=(time.perf_counter() - t0) * 1000,
            retrieved_chunks=retrieved,
        )
