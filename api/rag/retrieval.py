"""
Phase 4: Permission-Filtered Retrieval

Key design point from plan:
  vector_search(query, filter={"access_level": user.allowed_levels})

This PoC simulates vector similarity with random scores.
In production: replace _vector_search() with real VectorDB call
(Qdrant / Milvus / pgvector) that applies the metadata filter server-side.
"""
import random
from typing import Set

from api.auth.models import AccessLevel, User
from api.rag.models import RetrievedChunk
from api.store import doc_store, Document


def _vector_search(query: str, allowed_levels: Set[AccessLevel], top_k: int) -> list[Document]:
    """
    Simulate vector search with access_level filter.

    Real implementation would call:
        qdrant_client.search(
            collection_name=...,
            query_vector=embed(query),
            query_filter=Filter(
                must=[FieldCondition(
                    key="access_level",
                    match=MatchAny(any=[lvl.value for lvl in allowed_levels])
                )]
            ),
            limit=top_k,
        )
    """
    # Filter by permission BEFORE scoring — same logic as production metadata filter
    visible_docs = [d for d in doc_store if d.access_level in allowed_levels]

    # Simulate similarity scores (deterministic via hash for reproducibility)
    scored = []
    for doc in visible_docs:
        score = round(0.5 + 0.5 * (hash(query + doc.doc_id) % 100) / 100, 4)
        scored.append((doc, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def retrieve(query: str, user: User, top_k: int = 3) -> list[RetrievedChunk]:
    """
    Retrieve top_k chunks visible to this user.
    Permission filtering happens inside — callers never need to worry about it.
    """
    allowed = user.allowed_access_levels
    results = _vector_search(query, allowed, top_k)
    return [
        RetrievedChunk(
            doc_id=doc.doc_id,
            title=doc.title,
            content=doc.content,
            access_level=doc.access_level.value,
            score=score,
        )
        for doc, score in results
    ]
