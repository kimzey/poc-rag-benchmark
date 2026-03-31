"""
Phase 4: LINE Webhook Adapter

Channel Adapter Pattern:
  LINE Webhook → LINE Adapter → Core RAG Service (same as Web/Discord)

This adapter:
  1. Validates LINE signature (HMAC-SHA256)
  2. Extracts user message from LINE event format
  3. Calls the core RAG pipeline with a service account
  4. Sends reply back via LINE Messaging API

Design note: The RAG pipeline never knows it's talking to LINE.
The adapter translates LINE protocol ↔ internal ChatRequest/ChatResponse.
"""
import hashlib
import hmac
import os
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from api.auth.models import User, UserType
from api.rag.models import ChatMessage, ChatRequest
from api.rag.pipeline import run_rag

router = APIRouter(prefix="/webhooks/line", tags=["webhooks"])

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

# Service account used for LINE bot queries (customer-level access)
LINE_SERVICE_USER = User(
    user_id="svc_line",
    username="line_bot",
    user_type=UserType.customer,  # LINE users get customer access by default
)


def _verify_line_signature(body: bytes, signature: str) -> bool:
    """Validate X-Line-Signature header (HMAC-SHA256)."""
    if not LINE_CHANNEL_SECRET:
        return True  # Skip in dev/PoC when no secret is set
    mac = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    import base64
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def _reply_to_line(reply_token: str, text: str) -> None:
    """Send a reply message to LINE."""
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    async with httpx.AsyncClient() as client:
        await client.post(LINE_REPLY_URL, json=payload, headers=headers)


@router.post("", summary="LINE Messaging API webhook receiver")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(...),
) -> dict:
    """
    Receive LINE events, run RAG, reply back to LINE.

    This endpoint is the ONLY LINE-specific code.
    Everything downstream (retrieval, LLM) is channel-agnostic.
    """
    body = await request.body()
    if not _verify_line_signature(body, x_line_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid LINE signature",
        )

    data: dict[str, Any] = await request.json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        user_text: str = message["text"]
        reply_token: str = event["replyToken"]

        # Adapt LINE message → internal ChatRequest
        chat_request = ChatRequest(
            messages=[ChatMessage(role="user", content=user_text)],
            top_k=3,
        )

        # Run RAG with service account (could be per-LINE-user in production)
        response = await run_rag(chat_request, LINE_SERVICE_USER)

        # Adapt internal ChatResponse → LINE reply
        await _reply_to_line(reply_token, response.answer)

    return {"status": "ok"}
