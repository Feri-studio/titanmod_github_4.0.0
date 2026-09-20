from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database.db import ensure_chat, upsert_user, add_name_history, get_connection, get_settings, bump_stat


class ContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user:
            await upsert_user(user)
            await add_name_history(user)
            data["user"] = user

        message = event if isinstance(event, Message) else getattr(event, "message", None)
        chat = getattr(message, "chat", None) if message else None
        bot: Bot = data.get("bot")

        connected_id = None
        if user:
            connected_id = await get_connection(user.id)
        data["connected_chat_id"] = connected_id

        if chat and chat.type in ("group", "supergroup"):
            info = await ensure_chat(chat.id, chat.title, chat.type, getattr(chat, "username", None))
            data["chat_row"] = info
            data["settings"] = info.get("settings") or await get_settings(chat.id)
            data["mod_chat_id"] = chat.id
            if isinstance(event, Message) and not event.from_user is None:
                try:
                    await bump_stat(chat.id, "messages")
                except Exception:
                    pass
        elif connected_id:
            info = await ensure_chat(connected_id)
            data["chat_row"] = info
            data["settings"] = info.get("settings") or await get_settings(connected_id)
            data["mod_chat_id"] = connected_id
        else:
            data["settings"] = {}
            data["mod_chat_id"] = chat.id if chat else None

        return await handler(event, data)
