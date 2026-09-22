"""TitanMod 4.5 — inventory, rep, marriage, schedule, presets, forcesub, siege, modstats."""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions, ChatMemberUpdated
from aiogram.filters import Command, CommandObject

from config import config
from core.style import card, ok, fail, HR
from core.text import html_esc, mention
from filters.rank import RankOrAdminFilter
from filters.admin import IsAdminFilter, IsGroupFilter
from database.db import get_settings, update_settings
from database.extra import (
    inv_add, inv_list, inv_has,
    rep_vote, rep_get, rep_top,
    marry, divorce, get_spouse,
    schedule_post, bump_mod_stat, mod_stats_top,
)
from handlers.common import resolve_user, MUTE_PERMS, FREE_PERMS

router = Router()

PRESETS = {
    "soft": {
        "antiflood": 1, "flood_limit": 10, "antispam": 0, "welcome_captcha": 0,
        "raid_mode": 0, "filter_links": 0,
    },
    "normal": {
        "antiflood": 1, "flood_limit": 6, "antispam": 1, "welcome_captcha": 0,
        "raid_mode": 0, "filter_links": 0,
    },
    "strict": {
        "antiflood": 1, "flood_limit": 4, "antispam": 1, "welcome_captcha": 1,
        "raid_mode": 1, "filter_links": 1, "filter_forwards": 1,
    },
}


@router.message(Command("preset"), RankOrAdminFilter("settings"))
async def cmd_preset(message: Message, command: CommandObject):
    name = (command.args or "").strip().lower()
    if name not in PRESETS:
        await message.reply(
            "Пресеты автомода:\n"
            "• <code>/preset soft</code>\n"
            "• <code>/preset normal</code>\n"
            "• <code>/preset strict</code>"
        )
        return
    await update_settings(message.chat.id, **PRESETS[name])
    await message.reply(ok(f"Пресет <b>{name}</b> применён"))


@router.message(Command("forcesub"), RankOrAdminFilter("forcesub"))
async def cmd_forcesub(message: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if not arg or arg in ("off", "0", "нет"):
        await update_settings(message.chat.id, force_sub=0, force_sub_chat="")
        await message.reply(ok("Force-sub выключен"))
        return
    # @channel or -100id
    await update_settings(message.chat.id, force_sub=1, force_sub_chat=arg)
    await message.reply(ok(f"Force-sub: нужно быть в <code>{html_esc(arg)}</code>"))


@router.message(Command("siege", "осада"), RankOrAdminFilter("raid"))
async def cmd_siege(message: Message, bot: Bot, command: CommandObject):
    mins = 15
    if command.args and command.args.strip().isdigit():
        mins = max(5, min(120, int(command.args.strip())))
    try:
        await bot.set_chat_permissions(message.chat.id, MUTE_PERMS)
        await update_settings(
            message.chat.id,
            locked_until=1,
            raid_mode=1,
            siege_until=time.time() + mins * 60,
        )
        await message.reply(ok(f"Режим осады ~{mins} мин. Снять: /unfreeze или /siegeoff"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("siegeoff"), RankOrAdminFilter("raid"))
async def cmd_siegeoff(message: Message, bot: Bot):
    try:
        await bot.set_chat_permissions(message.chat.id, FREE_PERMS)
        await update_settings(message.chat.id, locked_until=0, raid_mode=0, siege_until=0)
        await message.reply(ok("Осада снята"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("newbie"), RankOrAdminFilter("settings"))
async def cmd_newbie(message: Message, command: CommandObject):
    """Minutes of restricted mode for new joins: /newbie 10 or /newbie off"""
    arg = (command.args or "").strip().lower()
    if arg in ("off", "0", "нет"):
        await update_settings(message.chat.id, newbie_minutes=0)
        await message.reply(ok("Карантин новичков выключен"))
        return
    if not arg.isdigit():
        await message.reply("<code>/newbie 15</code> — минут только текст без ссылок · /newbie off")
        return
    m = max(1, min(1440, int(arg)))
    await update_settings(message.chat.id, newbie_minutes=m)
    await message.reply(ok(f"Новички ограничены на <b>{m}</b> мин после входа"))


@router.message(Command("rep", "+rep", "-rep", "реп"))
async def cmd_rep(message: Message, bot: Bot, command: CommandObject):
    if message.chat.type == "private":
        return
    text = (message.text or "").split()[0].lower()
    value = -1 if text.startswith("/-") or text.startswith("-rep") else 1
    if command.args and command.args.strip().startswith("-"):
        value = -1
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user and message.reply_to_message:
        user = message.reply_to_message.from_user
    if not user:
        score = await rep_get(message.chat.id, message.from_user.id)
        await message.reply(f"Твоя репутация: <b>{score}</b>\nВыдать: ответом <code>/rep</code> или <code>/-rep</code>")
        return
    ok_v, msg, score = await rep_vote(message.chat.id, message.from_user.id, user.id, value)
    if not ok_v:
        await message.reply(fail(msg))
        return
    sign = "+" if value > 0 else ""
    await message.reply(ok(f"{sign}{value} реп → {mention(user)} · итог <b>{score}</b>"))


@router.message(Command("reptop", "топпеп"))
async def cmd_reptop(message: Message):
    if message.chat.type == "private":
        return
    rows = await rep_top(message.chat.id)
    if not rows:
        await message.reply("Репутация пока пустая")
        return
    lines = ["🏆 <b>Топ репутации</b>", HR]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. <code>{r['user_id']}</code> — <b>{r['score']}</b>")
    await message.reply("\n".join(lines))


@router.message(Command("marry", "брак"))
async def cmd_marry(message: Message, bot: Bot, command: CommandObject):
    if message.chat.type == "private":
        return
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user and message.reply_to_message:
        user = message.reply_to_message.from_user
    if not user:
        await message.reply("Ответь на сообщение: /marry")
        return
    if await get_spouse(message.chat.id, message.from_user.id):
        await message.reply(fail("Ты уже в браке. /divorce"))
        return
    if await get_spouse(message.chat.id, user.id):
        await message.reply(fail("Цель уже в браке"))
        return
    await marry(message.chat.id, message.from_user.id, user.id)
    await message.reply(ok(f"💍 {mention(message.from_user)} ❤️ {mention(user)}"))


@router.message(Command("divorce", "развод"))
async def cmd_divorce(message: Message):
    if message.chat.type == "private":
        return
    if await divorce(message.chat.id, message.from_user.id):
        await message.reply(ok("Брак расторгнут"))
    else:
        await message.reply("Ты не в браке")


@router.message(Command("spouse", "пара"))
async def cmd_spouse(message: Message):
    if message.chat.type == "private":
        return
    sp = await get_spouse(message.chat.id, message.from_user.id)
    if not sp:
        await message.reply("Нет пары. /marry ответом")
        return
    await message.reply(f"💍 Твоя пара: <code>{sp}</code>")


@router.message(Command("schedule", "отложить"), RankOrAdminFilter("settings"))
async def cmd_schedule(message: Message, command: CommandObject):
    """ /schedule 18:30 текст  or  /schedule 2h текст """
    raw = (command.args or "").strip()
    if not raw:
        await message.reply("<code>/schedule 18:30 текст</code> или <code>/schedule 2h текст</code>")
        return
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Нужны время и текст")
        return
    when_s, text = parts[0], parts[1]
    now = time.time()
    run_at = None
    if ":" in when_s and len(when_s) <= 5:
        try:
            hh, mm = map(int, when_s.split(":"))
            dt = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
            if dt.timestamp() < now:
                dt += timedelta(days=1)
            run_at = dt.timestamp()
        except Exception:
            pass
    else:
        from core.timeparse import parse_time
        sec = parse_time(when_s, 0)
        if sec:
            run_at = now + sec
    if not run_at:
        await message.reply(fail("Не понял время"))
        return
    pid = await schedule_post(message.chat.id, message.from_user.id, text, run_at)
    await message.reply(ok(f"Пост #{pid} запланирован на <code>{datetime.fromtimestamp(run_at).strftime('%d.%m %H:%M')}</code>"))


@router.message(Command("inventory", "инвентарь", "inv"))
async def cmd_inv(message: Message):
    if message.chat.type == "private":
        return
    items = await inv_list(message.chat.id, message.from_user.id)
    if not items:
        await message.reply("Инвентарь пуст. /shop")
        return
    lines = ["🎒 <b>Инвентарь</b>", HR]
    for it in items:
        exp = float(it.get("expires_at") or 0)
        extra = f" до {datetime.fromtimestamp(exp).strftime('%d.%m %H:%M')}" if exp else ""
        lines.append(f"• <code>{html_esc(it['item'])}</code> ×{it.get('qty', 1)}{extra}")
    await message.reply("\n".join(lines))


@router.message(Command("modstats", "статамодов"), RankOrAdminFilter("settings"))
async def cmd_modstats(message: Message):
    rows = await mod_stats_top(message.chat.id)
    if not rows:
        await message.reply("Пока нет статистики модерации")
        return
    lines = ["📊 <b>Стата модераторов</b>", HR]
    for r in rows:
        lines.append(f"• <code>{r['admin_id']}</code> — <b>{r['total']}</b> действий")
    await message.reply("\n".join(lines))


@router.message(Command("backupnow"), IsAdminFilter())
async def cmd_backupnow(message: Message, bot: Bot):
    """Send DB copy to BOT_ADMINS (owner)."""
    if not config.is_owner(message.from_user.id):
        await message.reply(fail("Только владелец бота"))
        return
    from database.db import DB_PATH
    import os
    if not os.path.exists(DB_PATH):
        await message.reply(fail("БД не найдена"))
        return
    from aiogram.types import FSInputFile
    doc = FSInputFile(DB_PATH, filename="moderation_bot_backup.db")
    sent = 0
    for aid in config.ADMINS:
        try:
            await bot.send_document(aid, doc, caption=f"Backup TitanMod {config.VERSION}")
            sent += 1
        except Exception:
            pass
    await message.reply(ok(f"Бэкап отправлен: {sent} получатель(ей)"))


@router.message(Command("warnladder"), RankOrAdminFilter("settings"))
async def cmd_warnladder(message: Message, command: CommandObject):
    """ /warnladder 3 mute | /warnladder 5 ban | /warnladder show """
    s = await get_settings(message.chat.id)
    arg = (command.args or "show").strip().lower()
    if arg == "show" or not arg:
        await message.reply(
            card(
                "Варн-лестница",
                f"Лимит: <b>{s.get('warn_limit', 3)}</b>\n"
                f"Действие: <b>{html_esc(str(s.get('warn_mode', s.get('warnmode', 'mute'))))}</b>\n"
                f"Смена: <code>/warnladder 3 mute</code> · <code>/warnladder 5 ban</code>",
                emoji="⚠️",
            )
        )
        return
    parts = arg.split()
    if len(parts) >= 1 and parts[0].isdigit():
        limit = max(1, min(20, int(parts[0])))
        mode = parts[1] if len(parts) > 1 else "mute"
        if mode not in ("mute", "ban", "kick", "tban"):
            mode = "mute"
        await update_settings(message.chat.id, warn_limit=limit, warn_mode=mode)
        await message.reply(ok(f"Лестница: {limit} варнов → <b>{mode}</b>"))
        return
    await message.reply("<code>/warnladder 3 mute</code>")


# Chat member: notify owners if bot demoted
@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated, bot: Bot):
    try:
        old = event.old_chat_member.status
        new = event.new_chat_member.status
        if old in ("administrator", "creator") and new not in ("administrator", "creator"):
            title = event.chat.title or str(event.chat.id)
            text = (
                f"⚠️ Бота сняли с админов в <b>{html_esc(title)}</b>\n"
                f"id: <code>{event.chat.id}</code>"
            )
            for aid in config.ADMINS:
                try:
                    await bot.send_message(aid, text)
                except Exception:
                    pass
    except Exception:
        pass
