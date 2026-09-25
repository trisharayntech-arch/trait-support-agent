"""
Security helpers.

NOTE (production caveat): the admin check here is a single shared API key
compared with a header, suitable for a prototype / internal demo only.
Before real deployment this must be replaced with proper authentication
(e.g., OAuth2/JWT with per-user identities and RBAC).
"""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from config.settings import get_settings


def verify_admin_key(x_admin_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        # Fail closed: if no admin key is configured, admin routes are unusable
        # rather than silently open.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access is not configured on this server.",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin credentials.",
        )
