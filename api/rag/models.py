"""
Phase 4: RAG Pydantic models
"""
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    collection: str | None = None   # optional: restrict to a collection
    top_k: int = 3
    stream: bool = False


class RetrievedChunk(BaseModel):
    doc_id: str
    title: str
    content: str
    access_level: str
    score: float  # similarity score (0-1)


class ChatResponse(BaseModel):
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    model: str
    usage: dict | None = None
