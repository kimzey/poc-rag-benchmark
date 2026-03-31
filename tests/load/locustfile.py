"""
Phase 5: Load Test — Scenario 4 (Concurrent queries under load)

Target metrics (from plan.md §9.2):
  p50 latency:  < 3s   (including LLM generation)
  p95 latency:  < 8s   (including LLM generation)
  Retrieval p95 < 200ms (vector search only)
  Throughput:   > 50 req/sec

Run (requires running API server):
  make load-test                      # headless, 50 users, 30s
  locust -f tests/load/locustfile.py  # interactive UI at http://localhost:8089

Note: With mock LLM (no OPENROUTER_API_KEY), latency will be sub-millisecond.
      With real LLM, expect 1-5s p50 depending on provider.
"""
from locust import HttpUser, between, task


class EmployeeUser(HttpUser):
    """Simulates an internal employee using the RAG chat and document search."""

    wait_time = between(0.5, 2)
    weight = 3  # 3x more employees than customers

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/token",
            json={"username": "bob_employee", "password": "emp123"},
        )
        token = r.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(4)
    def chat_query_en(self):
        self.client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "what is the return policy?"}],
                "top_k": 3,
            },
            headers=self.headers,
            name="/chat/completions [employee-en]",
        )

    @task(3)
    def chat_query_th(self):
        self.client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "นโยบายการลาพักร้อนเป็นอย่างไร?"}],
                "top_k": 3,
            },
            headers=self.headers,
            name="/chat/completions [employee-th]",
        )

    @task(2)
    def doc_search(self):
        self.client.get(
            "/api/v1/documents/search",
            params={"q": "policy", "top_k": 3},
            headers=self.headers,
            name="/documents/search",
        )

    @task(1)
    def list_collections(self):
        self.client.get(
            "/api/v1/documents/collections",
            headers=self.headers,
            name="/documents/collections",
        )


class CustomerUser(HttpUser):
    """Simulates an external customer querying the public-facing RAG."""

    wait_time = between(1, 4)
    weight = 1

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/token",
            json={"username": "carol_customer", "password": "cust123"},
        )
        token = r.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def chat_query_product(self):
        self.client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "สินค้ารับประกันกี่ปี?"}],
                "top_k": 3,
            },
            headers=self.headers,
            name="/chat/completions [customer-th]",
        )

    @task(2)
    def chat_query_return(self):
        self.client.post(
            "/api/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "how do I return a product?"}],
                "top_k": 3,
            },
            headers=self.headers,
            name="/chat/completions [customer-en]",
        )

    @task(1)
    def search_faq(self):
        self.client.get(
            "/api/v1/documents/search",
            params={"q": "warranty return", "top_k": 3},
            headers=self.headers,
            name="/documents/search [customer]",
        )
