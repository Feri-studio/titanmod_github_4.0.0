"""In-memory cache of recent messages for /snipe and /editsnipe."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Optional
import time

MAX_PER_CHAT = 40


@dataclass
class CachedMsg:
    message_id: int
    user_id: int
    username: str
    full_name: str
    text: str
    date: float
    edited: bool = False
    old_text: str = ""


_deleted: dict[int, Deque[CachedMsg]] = defaultdict(lambda: deque(maxlen=MAX_PER_CHAT))
_edited: dict[int, Deque[CachedMsg]] = defaultdict(lambda: deque(maxlen=MAX_PER_CHAT))
_recent: dict[int, dict[int, CachedMsg]] = defaultdict(dict)  # chat_id -> msg_id -> msg


def remember(chat_id: int, message_id: int, user_id: int, username: str, full_name: str, text: str) -> None:
    if not text:
        return
    cm = CachedMsg(
        message_id=message_id,
        user_id=user_id,
        username=username or "",
        full_name=full_name or str(user_id),
        text=text[:2000],
        date=time.time(),
    )
    bucket = _recent[chat_id]
    bucket[message_id] = cm
    # prune
    if len(bucket) > 200:
        for k in list(bucket.keys())[:80]:
            bucket.pop(k, None)


def mark_deleted(chat_id: int, message_id: int) -> Optional[CachedMsg]:
    cm = _recent[chat_id].pop(message_id, None)
    if cm:
        _deleted[chat_id].appendleft(cm)
    return cm


def mark_edited(chat_id: int, message_id: int, new_text: str) -> Optional[CachedMsg]:
    cm = _recent[chat_id].get(message_id)
    if not cm:
        return None
    old = cm.text
    cm.old_text = old
    cm.text = (new_text or "")[:2000]
    cm.edited = True
    snap = CachedMsg(
        message_id=cm.message_id,
        user_id=cm.user_id,
        username=cm.username,
        full_name=cm.full_name,
        text=cm.text,
        date=time.time(),
        edited=True,
        old_text=old,
    )
    _edited[chat_id].appendleft(snap)
    return snap


def last_deleted(chat_id: int) -> Optional[CachedMsg]:
    q = _deleted.get(chat_id)
    return q[0] if q else None


def last_edited(chat_id: int) -> Optional[CachedMsg]:
    q = _edited.get(chat_id)
    return q[0] if q else None
