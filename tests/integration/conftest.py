"""
Phase 5: Integration Test Fixtures

Shared fixtures for all 7 E2E test scenarios.
Uses FastAPI TestClient (in-process, no running server needed).
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="session")
def client():
    """Single TestClient for the whole test session."""
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, username: str, password: str) -> str:
    r = client.post("/api/v1/auth/token", json={"username": username, "password": password})
    assert r.status_code == 200, f"Login failed for {username}: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def employee_token(client):
    return _login(client, "bob_employee", "emp123")


@pytest.fixture(scope="session")
def customer_token(client):
    return _login(client, "carol_customer", "cust123")


@pytest.fixture(scope="session")
def admin_token(client):
    return _login(client, "alice_admin", "admin123")


@pytest.fixture
def employee_headers(employee_token):
    return {"Authorization": f"Bearer {employee_token}"}


@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def clean_doc_store():
    """Restore doc_store to its original state after a test that uploads docs."""
    from api import store
    original_len = len(store.doc_store)
    yield
    del store.doc_store[original_len:]
