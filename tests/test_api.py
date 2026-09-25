"""
Basic API tests using FastAPI's TestClient.

These do NOT require a live OpenAI key for the endpoints exercised here
(health check and admin auth rejection). Tests that would require an actual
LLM/embedding call are noted in the README under "Known Limitations /
Needs Testing" rather than faked here.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "TRAIT AI Customer Support Agent"


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_admin_documents_requires_auth(client):
    resp = client.get("/admin/documents")
    assert resp.status_code == 401


def test_admin_documents_rejects_wrong_key(client):
    resp = client.get("/admin/documents", headers={"X-Admin-Key": "wrong-key"})
    assert resp.status_code == 401


def test_admin_documents_accepts_correct_key(client):
    resp = client.get("/admin/documents", headers={"X-Admin-Key": "test-admin-key"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_chat_rejects_empty_message(client):
    resp = client.post("/chat", json={"session_id": "s1", "message": "   "})
    assert resp.status_code in (400, 422)
