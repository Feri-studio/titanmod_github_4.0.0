"""Track messages for snipe/editsnipe."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, Update

from services.message_cache import remember, mark_edited


class SnipeTrackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat and event.chat.type in ("group", "supergroup"):
            text = event.text or event.caption or ""
            user = event.from_user
            if user and text and not text.startswith("/"):
                remember(
                    event.chat.id,
                    event.message_id,
                    user.id,
                    user.username or "",
                    user.full_name or "",
                    text,
                )
            # edited messages
            if event.edit_date and user and text:
                mark_edited(event.chat.id, event.message_id, text)
        return await handler(event, data)
