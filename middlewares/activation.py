"""Block group usage until activated — with owner auto-activate and free basics."""
from __future__ import annotations

import os
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import config
from database.db import get_settings, update_settings


class GroupActivationMiddleware(BaseMiddleware):
    FREE = frozenset({
        "activate", "активировать", "claim", "разблок",
        "ping", "id", "help", "start", "commands", "botinfo", "whoami",
        "about", "version", "menu", "айди", "айдичата", "emojirand", "when", "pick", "percent", "ship", "b64", "userid", "chatid", "uptime",
        "rps", "guess", "roulette", "trivia", "article", "articles", "minigames",
        "статья", "статьи", "конституция", "compliment", "ball", "extras", "random", "time", "hash", "uuid", "password", "fact", "koap", "uk", "bj", "hangman",
    })

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
        cmd = ""
        if text.startswith("/"):
            cmd = text[1:].split()[0].split("@")[0].lower()

        if cmd in self.FREE:
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

        uid = event.from_user.id if event.from_user else 0
        if uid and config.is_owner(uid):
            try:
                await update_settings(chat.id, group_activated=1)
                data["settings"] = {**(settings or {}), "group_activated": 1}
            except Exception:
                pass
            return await handler(event, data)

        if os.getenv("AUTO_ACTIVATE", "").strip().lower() in ("1", "true", "yes", "on"):
            try:
                await update_settings(chat.id, group_activated=1)
                data["settings"] = {**(settings or {}), "group_activated": 1}
            except Exception:
                pass
            return await handler(event, data)

        if text.startswith("/"):
            await event.reply(
                "\n".join(
                    [
                        "🔒 <b>Чат ещё не открыт для бота</b>",
                        "━━━━━━━━━━━━━━━━━━━━",
                        "Сейчас доступны только базовые команды:",
                        "› <code>/ping</code> · <code>/help</code> · <code>/id</code>",
                        "",
                        "<b>Как включить всё</b>",
                        "› Владелец бота пишет любую команду — чат откроется",
                        f"› Или: <code>/activate {config.ACTIVATE_CODE or 'КОД'}</code>",
                        "› Либо в .env: <code>AUTO_ACTIVATE=1</code>",
                        "────────────────────",
                        "<i>TitanMod · защита от чужих групп</i>",
                    ]
                )
            )
        return None
