"""Simple anti-flood middleware."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.35):
        self.rate_limit = rate_limit
        self._last: Dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            now = time.monotonic()
            if now - self._last[uid] < self.rate_limit:
                return None
            self._last[uid] = now
        return await handler(event, data)
