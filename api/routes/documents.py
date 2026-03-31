"""
Phase 4: Document routes

POST /api/v1/documents/upload   — employee / admin only
GET  /api/v1/documents/search   — all authenticated users (permission-filtered)
POST /api/v1/documents/index    — employee / admin only
GET  /api/v1/collections        — all authenticated users
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from api.auth.dependencies import require_permission
from api.auth.models import AccessLevel, Permission, User
from api.rag.retrieval import retrieve
from api.rag.models import RetrievedChunk
from api.store import doc_store, Document

router = APIRouter(prefix="/documents", tags=["documents"])


class UploadResponse(BaseModel):
    doc_id: str
    message: str


class SearchResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]


@router.post("/upload", response_model=UploadResponse, summary="Upload a document (employee+)")
async def upload_document(
    file: UploadFile = File(...),
    access_level: AccessLevel = AccessLevel.internal_kb,
    user: User = Depends(require_permission(Permission.doc_upload)),
) -> UploadResponse:
    """
    Upload a document and assign its access level.
    In production: chunk → embed → upsert into VectorDB with access_level metadata.
    """
    content = (await file.read()).decode("utf-8", errors="ignore")
    doc_id = f"d{len(doc_store) + 1:03d}"
    doc_store.append(Document(
        doc_id=doc_id,
        title=file.filename or "untitled",
        content=content[:500],  # truncate for PoC
        access_level=access_level,
    ))
    return UploadResponse(doc_id=doc_id, message=f"Uploaded as {access_level.value}")


@router.get("/search", response_model=SearchResponse, summary="Search documents (permission-filtered)")
async def search_documents(
    q: str,
    top_k: int = 3,
    user: User = Depends(require_permission(Permission.doc_read)),
) -> SearchResponse:
    """
    Keyword/vector search — only returns docs the user is allowed to see.
    """
    chunks = retrieve(q, user, top_k=top_k)
    return SearchResponse(query=q, results=chunks)


@router.post("/index", summary="Trigger re-indexing (employee+)")
async def index_documents(
    user: User = Depends(require_permission(Permission.doc_index)),
) -> dict:
    """Trigger async indexing job. In production: enqueue to Celery / worker."""
    return {"message": "Indexing job enqueued", "triggered_by": user.username}


@router.get("/collections", summary="List available collections")
async def list_collections(
    user: User = Depends(require_permission(Permission.doc_read)),
) -> dict:
    """
    List document collections visible to this user.
    """
    visible_levels = [lvl.value for lvl in user.allowed_access_levels]
    return {
        "user": user.username,
        "user_type": user.user_type.value,
        "visible_access_levels": visible_levels,
        "total_visible_docs": sum(
            1 for d in doc_store if d.access_level in user.allowed_access_levels
        ),
    }
