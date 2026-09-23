"""Simple password session for the panel."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Optional

from config import config

SESSION_COOKIE = "titanmod_panel"
_sessions: set[str] = set()


def panel_password() -> str:
    return os.getenv("PANEL_PASSWORD", "") or os.getenv("ACTIVATE_CODE", config.ACTIVATE_CODE)


def make_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions.add(token)
    return token


def drop_session(token: Optional[str]) -> None:
    if token:
        _sessions.discard(token)


def valid_session(token: Optional[str]) -> bool:
    return bool(token) and token in _sessions


def check_password(password: str) -> bool:
    expected = panel_password()
    if not expected:
        return False
    return hmac.compare_digest(password.strip(), expected.strip())
