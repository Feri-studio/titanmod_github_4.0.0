"""Reports helpers — status listing only (create is in security.py)."""
from __future__ import annotations

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import config
from core.style import fail, HR
from core.text import html_esc
from core.permissions import admin_cache
from database.db import DB_PATH
import aiosqlite

router = Router()


@router.message(Command("reportlist", "жалобысписок"))
async def cmd_reportlist(message: Message):
    """List stored reports without conflicting with /reports toggle in security."""
    if message.chat.type == "private":
        return
    if not await admin_cache.is_admin(message.bot, message.chat.id, message.from_user.id) and not config.is_owner(message.from_user.id):
        await message.reply(fail("Только админы"))
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM reports WHERE chat_id=? ORDER BY id DESC LIMIT 15",
            (message.chat.id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]
    if not rows:
        await message.reply("Жалоб в базе нет")
        return
    lines = ["🚩 <b>Жалобы (БД)</b>", HR]
    for r in rows:
        lines.append(
            f"#{r.get('id')} · на <code>{r.get('target_id')}</code> · "
            f"{html_esc((r.get('reason') or '')[:60])}"
        )
    await message.reply("\n".join(lines))
