from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from database.extra import get_alias


class AliasMiddleware(BaseMiddleware):
    """Rewrite /кик → /kick when an alias is set for the chat."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        text = getattr(event, "text", None)
        chat = getattr(event, "chat", None)
        if text and chat and text.startswith("/") and chat.type in ("group", "supergroup"):
            token = text[1:].split()[0].split("@")[0]
            rest = text[len(text.split()[0]):]
            try:
                mapped = await get_alias(chat.id, token)
            except Exception:
                mapped = None
            if mapped and mapped != token:
                new_text = f"/{mapped}{rest}"
                try:
                    event = event.model_copy(update={"text": new_text})
                except Exception:
                    pass
        return await handler(event, data)
