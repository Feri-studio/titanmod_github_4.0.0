"""Anti-cheat middleware: rate limits, bots, input length."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from core.anticheat import anticheat


class AntiCheatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        # ignore other bots issuing commands
        if event.from_user.is_bot:
            return None

        text = (event.text or event.caption or "").strip()
        if not text.startswith("/"):
            return await handler(event, data)

        chk = anticheat.check_text(text)
        if not chk.ok:
            try:
                await event.reply(f"🛡 <b>Античит</b>\n{chk.reason}")
            except Exception:
                pass
            return None

        cmd = text[1:].split()[0].split("@")[0].lower()
        rate = anticheat.check_command_rate(event.from_user.id, cmd)
        if not rate.ok:
            try:
                await event.reply(f"🛡 <b>Антифлуд</b>\n{rate.reason}")
            except Exception:
                pass
            return None

        data["anticheat"] = anticheat
        return await handler(event, data)
