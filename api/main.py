"""
Phase 4: RAG API — FastAPI application entry point

Endpoints:
  POST /api/v1/auth/token                 — Login → JWT
  POST /api/v1/chat/completions           — RAG query (permission-filtered)
  POST /api/v1/documents/upload           — Upload document (employee+)
  GET  /api/v1/documents/search           — Search documents (permission-filtered)
  POST /api/v1/documents/index            — Trigger indexing (employee+)
  GET  /api/v1/documents/collections      — List visible collections
  GET  /api/v1/me                         — Current user info + permissions
  POST /api/v1/feedback                   — Submit feedback on RAG response
  POST /api/v1/webhooks/line              — LINE Messaging API adapter

Run:
  uvicorn api.main:app --reload
  or: make api-run
"""
from fastapi import Depends, FastAPI

from api.auth.dependencies import get_current_user
from api.auth.models import User
from api.config import settings
from api.routes.auth_routes import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.documents import router as documents_router
from api.routes.feedback import router as feedback_router
from api.routes.webhooks.line import router as line_router

app = FastAPI(
    title=settings.app_name,
    description="Phase 4 PoC — Omnichannel RAG API with JWT + RBAC + Permission-Filtered Retrieval",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

PREFIX = "/api/v1"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(chat_router, prefix=PREFIX)
app.include_router(documents_router, prefix=PREFIX)
app.include_router(feedback_router, prefix=PREFIX)
app.include_router(line_router, prefix=PREFIX)


@app.get(f"{PREFIX}/me", tags=["auth"], summary="Current user info + permissions")
async def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "user_type": user.user_type.value,
        "permissions": sorted(p.value for p in user.permissions),
        "allowed_access_levels": sorted(lvl.value for lvl in user.allowed_access_levels),
    }


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"message": f"{settings.app_name} — visit /docs for API reference"}
