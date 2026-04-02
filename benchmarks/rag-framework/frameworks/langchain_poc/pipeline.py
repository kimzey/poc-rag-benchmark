"""
LangChain RAG PoC — modern LCEL style (LangChain ≥ 0.2).

Key changes from legacy:
- RetrievalQA removed → LCEL pipe chain (retriever | prompt | llm | parser)
- langchain.text_splitter → langchain_text_splitters
- langchain.prompts → langchain_core.prompts
- openai_api_base → base_url
- RunnableParallel preserves source docs alongside the answer
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

# macOS: FAISS and PyTorch/HuggingFace both bundle libomp.dylib → duplicate OMP runtime crash
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

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


def _format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


class LangChainRAGPipeline(BaseRAGPipeline):
    """LangChain: TextLoader → FAISS → LCEL chain (RunnableParallel)."""

    def __init__(self) -> None:
        from langchain_openai import ChatOpenAI

        if config.EMBEDDING_MODEL.startswith("text-embedding"):
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(
                model=config.EMBEDDING_MODEL,
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
            )
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

        self._llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
            temperature=0.1,
            max_tokens=512,
        )
        self._vectorstore = None
        self._chain = None

    @property
    def name(self) -> str:
        return "langchain"

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        from langchain_community.document_loaders import TextLoader
        from langchain_community.vectorstores import FAISS
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import PromptTemplate
        from langchain_core.runnables import RunnableParallel, RunnablePassthrough
        from langchain_text_splitters import RecursiveCharacterTextSplitter

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

        retriever = self._vectorstore.as_retriever(search_kwargs={"k": config.TOP_K})
        prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)

        # LCEL — pattern from official LangChain docs (RAG with sources)
        chain_from_docs = (
            RunnablePassthrough.assign(context=lambda x: _format_docs(x["context"]))
            | prompt
            | self._llm
            | StrOutputParser()
        )
        self._chain = RunnableParallel(
            context=retriever,
            question=RunnablePassthrough(),
        ).assign(answer=chain_from_docs)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexStats(
            num_chunks=len(chunks),
            indexing_time_ms=elapsed_ms,
            framework=self.name,
        )

    def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:  # noqa: ARG002
        t0 = time.perf_counter()

        result = self._chain.invoke(question)

        sources = [doc.metadata.get("source", "") for doc in result["context"]]
        chunks = [doc.page_content for doc in result["context"]]

        return RAGResult(
            answer=result["answer"],
            sources=sources,
            latency_ms=(time.perf_counter() - t0) * 1000,
            retrieved_chunks=chunks,
        )
