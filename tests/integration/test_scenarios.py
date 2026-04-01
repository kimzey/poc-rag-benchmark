"""
Phase 5: Integration Test Scenarios

Covers all 7 scenarios defined in plan.md §9.1:

  1. Employee uploads document & queries it
  2. Customer queries — sees only allowed docs
  3. LINE user sends question & gets answer
  4. Concurrent queries under load
  5. Component swap test
  6. Error handling — LLM timeout
  7. Thai language end-to-end

Run: make test-integration
"""
import concurrent.futures
import json
import time
from io import BytesIO
from unittest.mock import AsyncMock, patch

import openai
import pytest


# ─── Scenario 1: Employee uploads document & queries it ───────────────────────

class TestScenario1EmployeeUploadAndQuery:
    """
    Components: API → Auth → Ingest → VectorDB (in-memory) → LLM (mock)
    """

    def test_upload_document(self, client, employee_headers, clean_doc_store):
        content = b"Complete guide to employee leave policy and annual leave entitlements."
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("leave_policy.txt", BytesIO(content), "text/plain")},
            params={"access_level": "internal_kb"},
            headers=employee_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "doc_id" in data
        assert data["doc_id"].startswith("d")
        assert "internal_kb" in data["message"]

    def test_uploaded_doc_appears_in_search(self, client, employee_headers, clean_doc_store):
        content = b"unique_marker_xyz: special internal training document"
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("training.txt", BytesIO(content), "text/plain")},
            params={"access_level": "internal_kb"},
            headers=employee_headers,
        )
        assert r.status_code == 200
        doc_id = r.json()["doc_id"]

        r = client.get(
            "/api/v1/documents/search",
            params={"q": "training document", "top_k": 5},
            headers=employee_headers,
        )
        assert r.status_code == 200
        doc_ids = [chunk["doc_id"] for chunk in r.json()["results"]]
        assert doc_id in doc_ids, f"Uploaded doc {doc_id} not found in search results"

    def test_upload_and_chat_query(self, client, employee_headers, clean_doc_store):
        content = b"The overtime compensation policy states 1.5x rate for weekdays."
        client.post(
            "/api/v1/documents/upload",
            files={"file": ("overtime.txt", BytesIO(content), "text/plain")},
            params={"access_level": "internal_kb"},
            headers=employee_headers,
        )
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "overtime compensation policy"}], "top_k": 3},
            headers=employee_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert len(data["retrieved_chunks"]) > 0
        # Employee should not see confidential docs in results
        for chunk in data["retrieved_chunks"]:
            assert chunk["access_level"] != "confidential_kb"

    def test_customer_cannot_upload(self, client, customer_headers):
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("hack.txt", BytesIO(b"test"), "text/plain")},
            headers=customer_headers,
        )
        assert r.status_code == 403


# ─── Scenario 2: Customer queries — sees only allowed docs ────────────────────

class TestScenario2CustomerPermissionFilter:
    """
    Components: API → Auth → Permission Filter → VectorDB
    """

    def test_customer_search_only_sees_customer_kb(self, client, customer_headers):
        r = client.get(
            "/api/v1/documents/search",
            params={"q": "policy warranty return", "top_k": 10},
            headers=customer_headers,
        )
        assert r.status_code == 200
        results = r.json()["results"]
        for chunk in results:
            assert chunk["access_level"] == "customer_kb", (
                f"Customer received {chunk['access_level']} doc '{chunk['title']}' — permission leak!"
            )

    def test_customer_chat_only_uses_customer_kb(self, client, customer_headers):
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "tell me everything you know"}], "top_k": 10},
            headers=customer_headers,
        )
        assert r.status_code == 200
        for chunk in r.json()["retrieved_chunks"]:
            assert chunk["access_level"] == "customer_kb"

    def test_employee_sees_more_than_customer(self, client, employee_headers, customer_headers):
        def count_visible(headers):
            r = client.get(
                "/api/v1/documents/collections",
                headers=headers,
            )
            assert r.status_code == 200
            return r.json()["total_visible_docs"]

        employee_count = count_visible(employee_headers)
        customer_count = count_visible(customer_headers)
        assert employee_count > customer_count, (
            f"Employee ({employee_count}) should see more docs than customer ({customer_count})"
        )

    def test_admin_sees_all_access_levels(self, client, admin_headers):
        r = client.get("/api/v1/documents/collections", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        visible = set(data["visible_access_levels"])
        assert visible == {"customer_kb", "internal_kb", "confidential_kb"}

    def test_unauthenticated_request_rejected(self, client):
        r = client.get("/api/v1/documents/search", params={"q": "test"})
        # FastAPI HTTPBearer returns 403 when Authorization header is absent
        assert r.status_code in (401, 403)


# ─── Scenario 3: LINE user sends question & gets answer ───────────────────────

class TestScenario3LineWebhookE2E:
    """
    Components: LINE Adapter → API → RAG Pipeline → Response
    LINE_CHANNEL_SECRET not set in tests → signature check skipped.
    _reply_to_line is patched to avoid real HTTP call to LINE.
    """

    def _line_payload(self, text: str) -> bytes:
        return json.dumps({
            "events": [{
                "type": "message",
                "replyToken": "test_reply_token_abc",
                "message": {"type": "text", "text": text},
            }]
        }).encode()

    def test_line_webhook_returns_ok(self, client):
        with patch("api.routes.webhooks.line._reply_to_line", new_callable=AsyncMock):
            r = client.post(
                "/api/v1/webhooks/line",
                content=self._line_payload("What is the return policy?"),
                headers={"Content-Type": "application/json", "X-Line-Signature": "dummy"},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_line_webhook_calls_reply(self, client):
        with patch("api.routes.webhooks.line._reply_to_line", new_callable=AsyncMock) as mock_reply:
            client.post(
                "/api/v1/webhooks/line",
                content=self._line_payload("product warranty"),
                headers={"Content-Type": "application/json", "X-Line-Signature": "dummy"},
            )
        mock_reply.assert_awaited_once()
        reply_token, reply_text = mock_reply.call_args[0]
        assert reply_token == "test_reply_token_abc"
        assert len(reply_text) > 0

    def test_line_webhook_non_message_event_ignored(self, client):
        payload = json.dumps({
            "events": [{"type": "follow", "replyToken": "tok"}]
        }).encode()
        with patch("api.routes.webhooks.line._reply_to_line", new_callable=AsyncMock) as mock_reply:
            r = client.post(
                "/api/v1/webhooks/line",
                content=payload,
                headers={"Content-Type": "application/json", "X-Line-Signature": "dummy"},
            )
        assert r.status_code == 200
        mock_reply.assert_not_awaited()

    def test_line_webhook_bad_signature_rejected(self, client):
        import os
        with patch.dict(os.environ, {"LINE_CHANNEL_SECRET": "real_secret_key"}):
            # Re-import to pick up env var — use the actual endpoint with a bad sig
            # The module already loaded so we patch the module-level variable
            with patch("api.routes.webhooks.line.LINE_CHANNEL_SECRET", "real_secret_key"):
                r = client.post(
                    "/api/v1/webhooks/line",
                    content=self._line_payload("test"),
                    headers={"Content-Type": "application/json", "X-Line-Signature": "bad_signature"},
                )
        assert r.status_code == 400


# ─── Scenario 4: Concurrent queries under load ────────────────────────────────

class TestScenario4ConcurrentQueries:
    """
    Components: API → VectorDB (in-memory) → LLM (mock)
    Uses ThreadPoolExecutor — FastAPI TestClient is thread-safe.
    """

    N_REQUESTS = 30
    MAX_WORKERS = 10

    def test_concurrent_chat_queries(self, client, employee_token):
        headers = {"Authorization": f"Bearer {employee_token}"}

        def make_request(i: int):
            queries = [
                "what is the return policy?",
                "นโยบายการลาพักร้อนเป็นอย่างไร?",
                "product warranty information",
            ]
            body = {
                "messages": [{"role": "user", "content": queries[i % len(queries)]}],
                "top_k": 3,
            }
            t0 = time.monotonic()
            r = client.post("/api/v1/chat/completions", json=body, headers=headers)
            elapsed = time.monotonic() - t0
            return r.status_code, elapsed

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as pool:
            results = list(pool.map(make_request, range(self.N_REQUESTS)))

        statuses = [r[0] for r in results]
        latencies = sorted(r[1] for r in results)

        assert all(s == 200 for s in statuses), (
            f"Some requests failed: {[s for s in statuses if s != 200]}"
        )

        p50 = latencies[int(self.N_REQUESTS * 0.50)]
        p95 = latencies[int(self.N_REQUESTS * 0.95)]

        print(f"\n  [{self.N_REQUESTS} concurrent reqs, {self.MAX_WORKERS} workers]")
        print(f"  p50={p50*1000:.0f}ms  p95={p95*1000:.0f}ms")

        # Mock LLM path — should be very fast (no network)
        assert p95 < 5.0, f"p95 latency too high: {p95:.3f}s"

    def test_concurrent_mixed_endpoints(self, client, employee_token, customer_token):
        def employee_search(_):
            hdrs = {"Authorization": f"Bearer {employee_token}"}
            return client.get("/api/v1/documents/search", params={"q": "policy"}, headers=hdrs).status_code

        def customer_chat(_):
            hdrs = {"Authorization": f"Bearer {customer_token}"}
            return client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "warranty?"}], "top_k": 2},
                headers=hdrs,
            ).status_code

        tasks = [employee_search] * 10 + [customer_chat] * 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            statuses = list(pool.map(lambda fn: fn(None), tasks))

        assert all(s == 200 for s in statuses)


# ─── Scenario 5: Component swap test ──────────────────────────────────────────

class TestScenario5ComponentSwap:
    """
    Verify the abstraction layer allows swapping the retrieval backend
    without changes to the pipeline or route layers.
    """

    def test_swap_retrieval_backend(self, client, employee_headers):
        from api.rag.models import RetrievedChunk

        mock_chunks = [
            RetrievedChunk(
                doc_id="swap001",
                title="Swapped Retriever Doc",
                content="This chunk comes from the swapped retrieval backend.",
                access_level="customer_kb",
                score=0.99,
            )
        ]

        with patch("api.rag.pipeline.retrieve", return_value=mock_chunks):
            r = client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "test query"}], "top_k": 1},
                headers=employee_headers,
            )

        assert r.status_code == 200
        data = r.json()
        chunks = data["retrieved_chunks"]
        assert len(chunks) == 1
        assert chunks[0]["doc_id"] == "swap001"
        assert chunks[0]["title"] == "Swapped Retriever Doc"

    def test_swap_retrieval_backend_search_route(self, client, employee_headers):
        from api.rag.models import RetrievedChunk

        alt_chunks = [
            RetrievedChunk(doc_id="alt001", title="Alt Backend", content="alt content",
                           access_level="internal_kb", score=0.88),
            RetrievedChunk(doc_id="alt002", title="Alt Backend 2", content="more alt content",
                           access_level="customer_kb", score=0.77),
        ]

        with patch("api.routes.documents.retrieve", return_value=alt_chunks):
            r = client.get(
                "/api/v1/documents/search",
                params={"q": "anything", "top_k": 2},
                headers=employee_headers,
            )

        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 2
        assert results[0]["doc_id"] == "alt001"

    def test_retrieval_interface_contract(self, client, employee_headers):
        """
        Verify the retrieve() signature contract: (query, user, top_k) → list[RetrievedChunk].
        Any backend that satisfies this contract is plug-and-play.
        """
        from api.rag import retrieval as retrieval_mod
        import inspect

        sig = inspect.signature(retrieval_mod.retrieve)
        params = list(sig.parameters.keys())
        assert params == ["query", "user", "top_k"], (
            f"retrieve() signature changed — would break component swap. Got: {params}"
        )


# ─── Scenario 6: Error handling — LLM timeout ─────────────────────────────────

class TestScenario6LLMErrorHandling:
    """
    Components: API → RAG Pipeline → Fallback behavior on LLM failure.
    """

    def test_llm_timeout_returns_503(self, client, employee_headers):
        with patch("api.rag.pipeline.settings") as mock_settings, \
             patch("api.rag.pipeline.AsyncOpenAI") as mock_openai_cls:

            mock_settings.openrouter_api_key = "fake-api-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_model = "gpt-4o-mini"

            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
                request=None  # type: ignore[arg-type]
            )
            mock_openai_cls.return_value = mock_client

            r = client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "what is the policy?"}], "top_k": 3},
                headers=employee_headers,
            )

        assert r.status_code == 503, f"Expected 503, got {r.status_code}: {r.text}"
        assert "unavailable" in r.json()["detail"].lower()

    def test_llm_connection_error_returns_503(self, client, employee_headers):
        with patch("api.rag.pipeline.settings") as mock_settings, \
             patch("api.rag.pipeline.AsyncOpenAI") as mock_openai_cls:

            mock_settings.openrouter_api_key = "fake-api-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_model = "gpt-4o-mini"

            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
                request=None  # type: ignore[arg-type]
            )
            mock_openai_cls.return_value = mock_client

            r = client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "policy question"}], "top_k": 3},
                headers=employee_headers,
            )

        assert r.status_code == 503

    def test_server_recovers_after_llm_error(self, client, employee_headers):
        """Verify subsequent requests work after an LLM error (server didn't crash)."""
        # First trigger a mock error
        with patch("api.rag.pipeline.settings") as mock_settings, \
             patch("api.rag.pipeline.AsyncOpenAI") as mock_openai_cls:

            mock_settings.openrouter_api_key = "fake-key"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
            mock_settings.openrouter_model = "gpt-4o-mini"

            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
                request=None  # type: ignore[arg-type]
            )
            mock_openai_cls.return_value = mock_client

            client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "trigger error"}], "top_k": 1},
                headers=employee_headers,
            )

        # Now verify the server still handles requests normally (mock LLM path)
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "return policy"}], "top_k": 3},
            headers=employee_headers,
        )
        assert r.status_code == 200

    def test_invalid_token_returns_401(self, client):
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test"}], "top_k": 1},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert r.status_code == 401

    def test_malformed_request_returns_422(self, client, employee_headers):
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": "not_a_list"},  # wrong type
            headers=employee_headers,
        )
        assert r.status_code == 422


# ─── Scenario 7: Thai language end-to-end ─────────────────────────────────────

class TestScenario7ThaiLanguageE2E:
    """
    Components: Thai query → Embed (simulated) → Retrieve → Thai-content response
    """

    THAI_QUERIES = [
        "นโยบายการลาพักร้อนเป็นอย่างไร?",
        "สินค้ารับประกันกี่ปี?",
        "นโยบายการคืนสินค้า",
        "สวัสดิการพนักงาน",
    ]

    def test_thai_query_retrieves_results(self, client, employee_headers):
        for query in self.THAI_QUERIES:
            r = client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": query}], "top_k": 3},
                headers=employee_headers,
            )
            assert r.status_code == 200, f"Failed for query: {query!r}"
            data = r.json()
            assert len(data["retrieved_chunks"]) > 0, (
                f"No chunks retrieved for Thai query: {query!r}"
            )

    def test_thai_search_returns_relevant_docs(self, client, employee_headers):
        r = client.get(
            "/api/v1/documents/search",
            params={"q": "นโยบาย", "top_k": 3},
            headers=employee_headers,
        )
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) > 0
        # HR Policy and policy docs contain Thai content
        titles = [chunk["title"] for chunk in results]
        assert any("Policy" in t or "FAQ" in t for t in titles), (
            f"Expected policy docs in results, got: {titles}"
        )

    def test_thai_customer_query_permission_respected(self, client, customer_headers):
        """Thai query from customer should still respect access control."""
        r = client.post(
            "/api/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "นโยบายการลาพักร้อน"}], "top_k": 5},
            headers=customer_headers,
        )
        assert r.status_code == 200
        # Customer must only see customer_kb even for Thai queries
        for chunk in r.json()["retrieved_chunks"]:
            assert chunk["access_level"] == "customer_kb"

    def test_feedback_on_thai_query(self, client, employee_headers):
        """Submit feedback on a Thai RAG response."""
        r = client.post(
            "/api/v1/feedback",
            json={"query_id": "q-thai-001", "rating": 5, "comment": "ตอบถูกต้อง"},
            headers=employee_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["feedback_id"].startswith("fb")
        assert data["message"] == "Feedback recorded"

    def test_feedback_invalid_rating_rejected(self, client, employee_headers):
        """Rating must be 1-5."""
        r = client.post(
            "/api/v1/feedback",
            json={"query_id": "q001", "rating": 0},
            headers=employee_headers,
        )
        assert r.status_code == 422

    def test_thai_line_webhook_query(self, client):
        """Thai language query via LINE webhook."""
        payload = json.dumps({
            "events": [{
                "type": "message",
                "replyToken": "thai_reply_token",
                "message": {"type": "text", "text": "สินค้ารับประกันกี่ปี?"},
            }]
        }).encode()

        with patch("api.routes.webhooks.line._reply_to_line", new_callable=AsyncMock) as mock_reply:
            r = client.post(
                "/api/v1/webhooks/line",
                content=payload,
                headers={"Content-Type": "application/json", "X-Line-Signature": "dummy"},
            )

        assert r.status_code == 200
        mock_reply.assert_awaited_once()
        _, reply_text = mock_reply.call_args[0]
        assert len(reply_text) > 0, "Reply to Thai LINE message was empty"
