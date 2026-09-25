"""FastAPI application entrypoint for the TRAIT AI Customer Support Agent."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import admin, chat, health
from config.settings import ensure_data_dirs, get_settings
from database.db import init_db
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="TRAIT AI Customer Support Agent",
    description="RAG-based customer support backend for TRAIT Innovation.",
    version="0.1.0",
)

# CORS is permissive for local development. Restrict allow_origins to the
# actual frontend domain(s) before deploying to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    settings = get_settings()
    ensure_data_dirs()
    init_db()
    logger.info("Startup complete. Environment=%s", settings.environment)
    if not settings.openai_api_key:
        logger.warning(
            "OPENAI_API_KEY is not set — chat and document ingestion will fail until configured."
        )


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/")
def root() -> dict:
    return {
        "service": "TRAIT AI Customer Support Agent",
        "docs": "/docs",
        "health": "/health",
    }
