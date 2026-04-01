"""
RAG API HTTP client — wraps httpx.AsyncClient with typed responses.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    content: str
    access_level: str
    score: float


@dataclass
class ChatResult:
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    model: str
    usage: dict | None = None


class AuthError(Exception):
    pass


class ServerConnectionError(Exception):
    pass


class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.current_user: dict | None = None
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    # ── internal ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── public API ────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            r = await self._http.get("/")
            return r.status_code == 200
        except Exception:
            return False

    async def login(self, username: str, password: str) -> dict:
        try:
            r = await self._http.post(
                "/api/v1/auth/token",
                json={"username": username, "password": password},
            )
        except httpx.ConnectError as exc:
            raise ServerConnectionError(f"Cannot reach {self.base_url}") from exc
        if r.status_code == 401:
            raise AuthError("Invalid username or password")
        r.raise_for_status()
        self.token = r.json()["access_token"]
        self.current_user = await self.me()
        return self.current_user

    async def me(self) -> dict:
        r = await self._http.get("/api/v1/me", headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def chat(
        self,
        messages: list[dict],
        top_k: int = 3,
        collection: str | None = None,
    ) -> ChatResult:
        payload: dict = {"messages": messages, "top_k": top_k}
        if collection:
            payload["collection"] = collection
        r = await self._http.post(
            "/api/v1/chat/completions",
            json=payload,
            headers=self._headers(),
        )
        r.raise_for_status()
        data = r.json()
        chunks = [RetrievedChunk(**c) for c in data.get("retrieved_chunks", [])]
        return ChatResult(
            answer=data["answer"],
            retrieved_chunks=chunks,
            model=data.get("model", "unknown"),
            usage=data.get("usage"),
        )

    async def search(self, query: str, top_k: int = 5) -> dict:
        r = await self._http.get(
            "/api/v1/documents/search",
            params={"q": query, "top_k": top_k},
            headers=self._headers(),
        )
        r.raise_for_status()
        return r.json()

    async def list_collections(self) -> dict:
        r = await self._http.get("/api/v1/documents/collections", headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def upload_document(self, file_path: str, access_level: str = "internal_kb") -> dict:
        import asyncio
        import os

        def _read() -> bytes:
            with open(file_path, "rb") as f:
                return f.read()

        content = await asyncio.to_thread(_read)
        filename = os.path.basename(file_path)
        r = await self._http.post(
            "/api/v1/documents/upload",
            files={"file": (filename, content, "text/plain")},
            params={"access_level": access_level},
            headers=self._headers(),
        )
        r.raise_for_status()
        return r.json()

    async def submit_feedback(
        self, query_id: str, rating: int, comment: str = ""
    ) -> dict:
        r = await self._http.post(
            "/api/v1/feedback",
            json={"query_id": query_id, "rating": rating, "comment": comment or None},
            headers=self._headers(),
        )
        r.raise_for_status()
        return r.json()

    def logout(self) -> None:
        self.token = None
        self.current_user = None

    async def close(self) -> None:
        await self._http.aclose()

    @property
    def is_logged_in(self) -> bool:
        return self.token is not None
