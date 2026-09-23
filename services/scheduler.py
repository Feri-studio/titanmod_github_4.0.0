import asyncio
import time
from aiogram import Bot
from config import config
from database.db import due_reminders, expired_captchas, del_captcha
from database.extra import due_giveaways, due_scheduled, mark_scheduled_done
from core.text import mention


async def scheduler_loop(bot: Bot):
    while True:
        try:
            await _tick(bot)
        except Exception:
            pass
        await asyncio.sleep(config.SCHEDULER_TICK)


async def _tick(bot: Bot):
    now = time.time()
    for r in await due_reminders(now):
        try:
            await bot.send_message(r["chat_id"], f"Напоминание для <a href='tg://user?id={r['user_id']}'>тебя</a>: {r['text']}")
        except Exception:
            try:
                await bot.send_message(r["user_id"], f"Напоминание: {r['text']}")
            except Exception:
                pass
    for c in await expired_captchas(now):
        try:
            if c.get("message_id"):
                await bot.delete_message(c["chat_id"], c["message_id"])
        except Exception:
            pass
        s_kick = True
        try:
            from database.db import get_settings
            s = await get_settings(c["chat_id"])
            s_kick = bool(s.get("captcha_kick", 1))
        except Exception:
            pass
        try:
            if s_kick:
                await bot.ban_chat_member(c["chat_id"], c["user_id"])
                await bot.unban_chat_member(c["chat_id"], c["user_id"])
        except Exception:
            pass
        await del_captcha(c["chat_id"], c["user_id"])
    try:
        from handlers.giveaway import finish_giveaway
        for g in await due_giveaways(now):
            await finish_giveaway(bot, g["id"])
    except Exception:
        pass
    try:
        await _scheduled_posts(bot)
    except Exception:
        pass
    try:
        await _daily_backup(bot)
    except Exception:
        pass


async def _scheduled_posts(bot: Bot):
    import time
    now = time.time()
    for row in await due_scheduled(now):
        try:
            await bot.send_message(row["chat_id"], row["text"])
        except Exception:
            pass
        try:
            await mark_scheduled_done(row["id"])
        except Exception:
            pass


# patch _tick via wrap - append call by replacing end of _tick


_last_backup_day = ""


async def _daily_backup(bot: Bot):
    """Once per calendar day send DB to BOT_ADMINS."""
    global _last_backup_day
    from datetime import date
    from config import config
    import os
    day = date.today().isoformat()
    if day == _last_backup_day:
        return
    # run after 03:00 local to avoid spam at midnight restarts
    import datetime as dt
    if dt.datetime.now().hour < 3:
        return
    from database.db import DB_PATH
    if not os.path.exists(DB_PATH):
        return
    from aiogram.types import FSInputFile
    doc = FSInputFile(DB_PATH, filename=f"titanmod-{day}.db")
    for aid in getattr(config, "ADMINS", []) or []:
        try:
            await bot.send_document(aid, doc, caption=f"Автобэкап TitanMod {config.VERSION} · {day}")
        except Exception:
            pass
    _last_backup_day = day
