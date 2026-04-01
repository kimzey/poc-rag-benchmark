"""
Haystack v2 RAG PoC.

Observations to note during evaluation:
- Pipeline is a DAG of components connected by named sockets
- Components are strongly-typed; connections are validated at pipeline build time
- Debugging: pipeline.draw() visualises the DAG
- Warm-up: components load models lazily on first run_pipeline call
- include_outputs_from lets you inspect intermediate component outputs
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

logging.getLogger("haystack").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from base import BaseRAGPipeline, IndexStats, RAGResult

_PROMPT_TEMPLATE = """\
You are a helpful assistant. Answer using ONLY the context below.
If the answer is not in the context, say \
"ไม่พบข้อมูลในเอกสาร (No information found in documents)."

Context:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}

Question: {{ question }}

Answer:"""


class HaystackRAGPipeline(BaseRAGPipeline):
    """Haystack 2.x: InMemoryDocumentStore → embedding retrieval → PromptBuilder → OpenAIGenerator."""

    def __init__(self) -> None:
        from haystack.document_stores.in_memory import InMemoryDocumentStore

        self._doc_store = InMemoryDocumentStore()
        self._use_openai_embed = config.EMBEDDING_MODEL.startswith("text-embedding")

        if self._use_openai_embed:
            from haystack.components.embedders import OpenAIDocumentEmbedder
            from haystack.utils import Secret
            self._doc_embedder = OpenAIDocumentEmbedder(
                model=config.EMBEDDING_MODEL,
                api_key=Secret.from_token(config.OPENAI_API_KEY),
            )
        else:
            from haystack.components.embedders import SentenceTransformersDocumentEmbedder
            self._doc_embedder = SentenceTransformersDocumentEmbedder(
                model=config.EMBEDDING_MODEL, progress_bar=False
            )
            self._doc_embedder.warm_up()
        self._pipeline = None

    @property
    def name(self) -> str:
        return "haystack"

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
        from haystack import Document, Pipeline
        from haystack.components.builders import PromptBuilder
        from haystack.components.generators import OpenAIGenerator
        from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
        from haystack.utils import Secret

        t0 = time.perf_counter()

        # Build document store
        raw_docs: list[Document] = []
        for path in doc_paths:
            text = Path(path).read_text(encoding="utf-8")
            for i, chunk in enumerate(self._chunk_text(text)):
                raw_docs.append(
                    Document(content=chunk, meta={"source": str(path), "chunk_id": i})
                )

        embedded_docs = self._doc_embedder.run(raw_docs)["documents"]
        self._doc_store.write_documents(embedded_docs)

        # Build query pipeline (DAG)
        self._pipeline = Pipeline()
        if self._use_openai_embed:
            from haystack.components.embedders import OpenAITextEmbedder
            query_embedder = OpenAITextEmbedder(
                model=config.EMBEDDING_MODEL,
                api_key=Secret.from_token(config.OPENAI_API_KEY),
            )
        else:
            from haystack.components.embedders import SentenceTransformersTextEmbedder
            query_embedder = SentenceTransformersTextEmbedder(
                model=config.EMBEDDING_MODEL, progress_bar=False
            )
        self._pipeline.add_component("embedder", query_embedder)
        self._pipeline.add_component(
            "retriever",
            InMemoryEmbeddingRetriever(
                document_store=self._doc_store, top_k=config.TOP_K
            ),
        )
        self._pipeline.add_component(
            "prompt_builder", PromptBuilder(template=_PROMPT_TEMPLATE)
        )
        self._pipeline.add_component(
            "llm",
            OpenAIGenerator(
                model=config.LLM_MODEL,
                api_key=Secret.from_token(config.OPENROUTER_API_KEY),
                api_base_url=config.OPENROUTER_BASE_URL,
                generation_kwargs={"temperature": 0.1, "max_tokens": 512},
            ),
        )

        # Connect sockets
        self._pipeline.connect("embedder.embedding", "retriever.query_embedding")
        self._pipeline.connect("retriever.documents", "prompt_builder.documents")
        self._pipeline.connect("prompt_builder.prompt", "llm.prompt")

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexStats(
            num_chunks=len(raw_docs),
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
        t0 = time.perf_counter()

        result = self._pipeline.run(
            {
                "embedder": {"text": question},
                "prompt_builder": {"question": question},
            },
            include_outputs_from={"retriever"},
        )

        answer = (result.get("llm") or {}).get("replies", [""])[0]
        retrieved_docs = (result.get("retriever") or {}).get("documents", [])
        sources = [d.meta.get("source", "") for d in retrieved_docs]
        chunks = [d.content for d in retrieved_docs]

        return RAGResult(
            answer=answer,
            sources=sources,
            latency_ms=(time.perf_counter() - t0) * 1000,
            retrieved_chunks=chunks,
        )
