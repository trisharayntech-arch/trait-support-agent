"""Thin HTTP client the Streamlit frontend uses to talk to the FastAPI backend."""
from __future__ import annotations

import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30


def send_chat_message(session_id: str, message: str) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/chat",
        json={"session_id": session_id, "message": message},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_chat_history(session_id: str) -> dict:
    resp = requests.get(f"{BACKEND_URL}/chat/history/{session_id}", timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def request_escalation(session_id: str, reason: str) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/chat/escalate",
        json={"session_id": session_id, "reason": reason},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def upload_document(admin_key: str, filename: str, file_bytes: bytes) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/admin/documents",
        headers={"X-Admin-Key": admin_key},
        files={"file": (filename, file_bytes)},
        timeout=DEFAULT_TIMEOUT,
    )
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise RuntimeError(detail)
    return resp.json()


def list_documents(admin_key: str) -> list[dict]:
    resp = requests.get(
        f"{BACKEND_URL}/admin/documents", headers={"X-Admin-Key": admin_key}, timeout=DEFAULT_TIMEOUT
    )
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise RuntimeError(detail)
    return resp.json()


def delete_document(admin_key: str, document_id: int) -> None:
    resp = requests.delete(
        f"{BACKEND_URL}/admin/documents/{document_id}",
        headers={"X-Admin-Key": admin_key},
        timeout=DEFAULT_TIMEOUT,
    )
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise RuntimeError(detail)


def list_escalations(admin_key: str, status_filter: str | None = None) -> list[dict]:
    params = {"status_filter": status_filter} if status_filter else {}
    resp = requests.get(
        f"{BACKEND_URL}/admin/escalations",
        headers={"X-Admin-Key": admin_key},
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise RuntimeError(detail)
    return resp.json()


def resolve_escalation(admin_key: str, escalation_id: int) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/admin/escalations/{escalation_id}/resolve",
        headers={"X-Admin-Key": admin_key},
        timeout=DEFAULT_TIMEOUT,
    )
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise RuntimeError(detail)
    return resp.json()


def check_health() -> dict:
    resp = requests.get(f"{BACKEND_URL}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()
