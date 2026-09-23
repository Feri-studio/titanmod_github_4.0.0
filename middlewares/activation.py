"""Block group usage until /activate with secret code."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from database.db import get_settings


class GroupActivationMiddleware(BaseMiddleware):
    ALLOW = frozenset({"activate", "активировать", "claim", "разблок"})

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        chat = event.chat
        if not chat or chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        text = (event.text or event.caption or "").strip()
        if text.startswith("/"):
            cmd = text[1:].split()[0].split("@")[0].lower()
            if cmd in self.ALLOW:
                return await handler(event, data)

        settings = data.get("settings")
        if settings is None:
            try:
                settings = await get_settings(chat.id)
                data["settings"] = settings
            except Exception:
                settings = {}

        if settings.get("group_activated") in (1, True, "1", "true", "on"):
            return await handler(event, data)

        if text.startswith("/"):
            await event.reply(
                "\n".join(
                    [
                        "🔒 <b>Группа не активирована</b>",
                        "━━━━━━━━━━━━━━━━━━━━",
                        "Бот уже в чате, но <b>не работает</b> без кода владельца.",
                        "",
                        "<b>Как включить</b>",
                        "› Только владелец бота пишет сюда:",
                        "  <code>/activate КОД</code>",
                        "",
                        "Без активации: баны, муты, экономика, настройки — выключены.",
                        "────────────────────",
                        "<i>TitanMod · доступ в группы только по коду</i>",
                    ]
                )
            )
        return None
