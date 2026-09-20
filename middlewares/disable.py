from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from database.db import is_disabled, get_settings


class DisableCommandMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)
        text = event.text
        if not text.startswith("/"):
            return await handler(event, data)
        cmd = text[1:].split()[0].split("@")[0].lower()
        chat = event.chat
        if chat.type not in ("group", "supergroup"):
            return await handler(event, data)
        if await is_disabled(chat.id, cmd):
            settings = data.get("settings") or await get_settings(chat.id)
            if settings.get("disable_delete"):
                try:
                    await event.delete()
                except Exception:
                    pass
            return None
        return await handler(event, data)
