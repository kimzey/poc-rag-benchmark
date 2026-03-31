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
from sentence_transformers import SentenceTransformer

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


class BareMetalRAGPipeline(BaseRAGPipeline):
    """Direct implementation: sentence-transformers + numpy cosine sim + OpenRouter."""

    def __init__(self) -> None:
        self._embedder = SentenceTransformer(config.EMBEDDING_MODEL)
        self._llm = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )
        self._chunks: list[str] = []
        self._sources: list[str] = []
        self._embeddings: np.ndarray | None = None

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

        self._embeddings = self._embedder.encode(
            self._chunks,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexStats(
            num_chunks=len(self._chunks),
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
        t0 = time.perf_counter()

        q_emb = self._embedder.encode([question], normalize_embeddings=True)[0]
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
