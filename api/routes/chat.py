"""
Phase 4: Chat routes — POST /api/v1/chat/completions
"""
from fastapi import APIRouter, Depends

from api.auth.dependencies import get_current_user, require_permission
from api.auth.models import Permission, User
from api.rag.models import ChatRequest, ChatResponse
from api.rag.pipeline import run_rag

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/completions",
    response_model=ChatResponse,
    summary="RAG query — permission-filtered retrieval + LLM answer",
)
async def chat_completions(
    body: ChatRequest,
    user: User = Depends(require_permission(Permission.chat_query)),
) -> ChatResponse:
    """
    Main RAG endpoint.
    - Retrieves only documents the authenticated user is allowed to see.
    - Calls LLM via OpenRouter (or mock if no key).
    """
    return await run_rag(body, user)
