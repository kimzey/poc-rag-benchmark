"""
LangChain RAG PoC.

Observations to note during evaluation:
- LCEL (LangChain Expression Language) is the modern API — pipe syntax (|)
- RetrievalQA is legacy but easier to understand; LCEL shown as alternative
- HuggingFaceEmbeddings wraps sentence-transformers transparently
- FAISS used for in-memory vector store (no server needed)
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

logging.getLogger("langchain").setLevel(logging.WARNING)
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
{context}

Question: {question}

Answer:"""


class LangChainRAGPipeline(BaseRAGPipeline):
    """LangChain: TextLoader → FAISS → RetrievalQA chain (LCEL variant noted in comments)."""

    def __init__(self) -> None:
        from langchain_openai import ChatOpenAI

        if config.EMBEDDING_MODEL.startswith("text-embedding"):
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(
                model=config.EMBEDDING_MODEL,
                openai_api_key=config.OPENROUTER_API_KEY,
                openai_api_base=config.OPENROUTER_BASE_URL,
            )
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        self._llm = ChatOpenAI(
            model=config.LLM_MODEL,
            openai_api_key=config.OPENROUTER_API_KEY,
            openai_api_base=config.OPENROUTER_BASE_URL,
            temperature=0.1,
            max_tokens=512,
        )
        self._vectorstore = None
        self._chain = None

    @property
    def name(self) -> str:
        return "langchain"

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        from langchain.prompts import PromptTemplate
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import TextLoader
        from langchain_community.vectorstores import FAISS

        # Legacy chain import — still works, mirrors how most tutorials are written
        from langchain.chains import RetrievalQA

        t0 = time.perf_counter()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )

        docs = []
        for path in doc_paths:
            loader = TextLoader(path, encoding="utf-8")
            docs.extend(loader.load())

        chunks = splitter.split_documents(docs)
        self._vectorstore = FAISS.from_documents(chunks, self._embeddings)

        prompt = PromptTemplate(
            template=_PROMPT_TEMPLATE,
            input_variables=["context", "question"],
        )

        # Legacy chain — for LCEL equivalent see: vectorstore.as_retriever() | prompt | llm
        self._chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            chain_type="stuff",
            retriever=self._vectorstore.as_retriever(
                search_kwargs={"k": config.TOP_K}
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexStats(
            num_chunks=len(chunks),
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
        t0 = time.perf_counter()

        result = self._chain.invoke({"query": question})

        sources = [doc.metadata.get("source", "") for doc in result["source_documents"]]
        chunks = [doc.page_content for doc in result["source_documents"]]

        return RAGResult(
            answer=result["result"],
            sources=sources,
            latency_ms=(time.perf_counter() - t0) * 1000,
            retrieved_chunks=chunks,
        )
