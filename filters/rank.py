"""Permission filter: Telegram admin OR bot rank with required perm."""
from __future__ import annotations

from typing import Union

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import config
from core.permissions import admin_cache
from core.ranks import has_perm, perm_for_command


class RankOrAdminFilter(BaseFilter):
    """Allow if BOT_ADMINS, Telegram chat admin, or rank has `perm`."""

    def __init__(self, perm: str | None = None, command: str | None = None):
        self.perm = perm or (perm_for_command(command) if command else None) or "warn"

    async def __call__(self, event: Union[Message, CallbackQuery], bot: Bot) -> bool:
        user = event.from_user
        if not user:
            return False
        if config.is_owner(user.id):
            return True
        message = event.message if isinstance(event, CallbackQuery) else event
        if not message or not message.chat:
            return False
        if message.chat.type not in ("group", "supergroup"):
            return False
        chat_id = message.chat.id
        # Telegram admin always allowed for moderation
        if await admin_cache.is_admin(bot, chat_id, user.id):
            return True
        return await has_perm(bot, chat_id, user.id, self.perm)
