from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from typing import Union

from config import config
from core.permissions import admin_cache
from database.db import get_connection


class IsGroupFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in ("group", "supergroup")


class IsPrivateFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"


class IsOwnerFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        uid = event.from_user.id if event.from_user else 0
        return config.is_owner(uid)


class IsAdminFilter(BaseFilter):
    def __init__(self, allow_private_connected: bool = True):
        self.allow_private_connected = allow_private_connected

    async def __call__(self, event: Union[Message, CallbackQuery], bot: Bot) -> bool:
        user = event.from_user
        if not user:
            return False
        if config.is_owner(user.id):
            return True
        if isinstance(event, CallbackQuery):
            message = event.message
        else:
            message = event
        if not message or not message.chat:
            return False
        if message.chat.type == "private":
            if not self.allow_private_connected:
                return False
            chat_id = await get_connection(user.id)
            if not chat_id:
                return False
            return await admin_cache.is_admin(bot, chat_id, user.id)
        return await admin_cache.is_admin(bot, message.chat.id, user.id)
