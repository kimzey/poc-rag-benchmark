"""
LlamaIndex RAG PoC.

Observations to note during evaluation:
- Settings is global state → watch for conflicts when running multiple frameworks
- SimpleDirectoryReader handles multiple formats automatically
- Query engine abstracts retrieval+generation into one call
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

logging.getLogger("llama_index").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from base import BaseRAGPipeline, IndexStats, RAGResult

_RAG_PROMPT = (
    "You are a helpful assistant. Answer using ONLY the provided context.\n"
    "If the answer is not in the context, say "
    "'ไม่พบข้อมูลในเอกสาร (No information found in documents).'\n\n"
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Query: {query_str}\n"
    "Answer: "
)


class LlamaIndexRAGPipeline(BaseRAGPipeline):
    """LlamaIndex: SimpleDirectoryReader → VectorStoreIndex → QueryEngine."""

    def __init__(self) -> None:
        from llama_index.core import Settings
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        from llama_index.llms.openai import OpenAI as LlamaOpenAI

        Settings.llm = LlamaOpenAI(
            model=config.LLM_MODEL,
            api_key=config.OPENROUTER_API_KEY,
            api_base=config.OPENROUTER_BASE_URL,
            temperature=0.1,
            max_tokens=512,
        )
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)
        Settings.chunk_size = config.CHUNK_SIZE
        Settings.chunk_overlap = config.CHUNK_OVERLAP

        self._index = None
        self._query_engine = None

    @property
    def name(self) -> str:
        return "llamaindex"

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
        from llama_index.core.prompts import PromptTemplate

        t0 = time.perf_counter()

        docs = SimpleDirectoryReader(input_files=doc_paths).load_data()
        self._index = VectorStoreIndex.from_documents(docs, show_progress=False)
        self._query_engine = self._index.as_query_engine(
            similarity_top_k=config.TOP_K,
            text_qa_template=PromptTemplate(_RAG_PROMPT),
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        num_chunks = len(self._index.docstore.docs)
        return IndexStats(
            num_chunks=num_chunks,
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
        t0 = time.perf_counter()

        response = self._query_engine.query(question)

        sources = [n.metadata.get("file_path", "") for n in response.source_nodes]
        chunks = [n.text for n in response.source_nodes]

        return RAGResult(
            answer=str(response),
            sources=sources,
            latency_ms=(time.perf_counter() - t0) * 1000,
            retrieved_chunks=chunks,
        )
