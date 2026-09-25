"""Shared pytest fixtures. Ensures tests use an isolated temp data directory."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure project root is importable when running `pytest` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Point SQLite and Chroma at a temp directory for every test, and clear settings cache."""
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    monkeypatch.setenv("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    from config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
