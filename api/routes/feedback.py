"""
Phase 4: Feedback routes — POST /api/v1/feedback

Collects user feedback on RAG responses for quality monitoring.
In production: store in PostgreSQL for analytics and model improvement.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth.dependencies import require_permission
from api.auth.models import Permission, User

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    query_id: str = Field(..., description="ID of the query/response being rated")
    rating: int = Field(..., ge=1, le=5, description="1-5 rating (5 = best)")
    comment: str | None = Field(None, description="Optional text feedback")


class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str


# In-memory store for PoC — production would use PostgreSQL
feedback_store: list[dict] = []


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback on a RAG response",
)
async def submit_feedback(
    body: FeedbackRequest,
    user: User = Depends(require_permission(Permission.chat_query)),
) -> FeedbackResponse:
    """
    Collect user feedback on RAG answer quality.
    Any user with chat:query permission can submit feedback.
    """
    feedback_id = f"fb{len(feedback_store) + 1:03d}"
    feedback_store.append({
        "feedback_id": feedback_id,
        "query_id": body.query_id,
        "rating": body.rating,
        "comment": body.comment,
        "user_id": user.user_id,
        "username": user.username,
    })
    return FeedbackResponse(
        feedback_id=feedback_id,
        message="Feedback recorded",
    )
