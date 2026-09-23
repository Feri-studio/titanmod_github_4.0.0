"""Fun pack — only extras not covered by handlers/fun.py."""
from __future__ import annotations

import random

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import card

router = Router()


@router.message(Command("roll", "кубик"))
async def cmd_roll(message: Message, command: CommandObject):
    arg = (command.args or "100").strip()
    sides = 100
    if arg.isdigit():
        sides = max(2, min(1000, int(arg)))
    await message.reply(card("Roll", f"d{sides}: <b>{random.randint(1, sides)}</b>", emoji="🎲"))
