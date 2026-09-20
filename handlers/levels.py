from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc, mention
from database.extra import add_xp, get_xp, set_xp, top_xp, reset_xp
from database.db import get_settings, update_settings, ensure_chat
from handlers.common import resolve_user

router = Router()


def rank_name(level: int) -> str:
    ranks = [
        (1, "Новичок"),
        (3, "Гость"),
        (5, "Участник"),
        (8, "Постоялец"),
        (12, "Активист"),
        (16, "Ветеран"),
        (20, "Старейшина"),
        (25, "Легенда"),
        (35, "Миф"),
        (50, "Титан"),
        (80, "Архитектор"),
        (120, "Хранитель"),
    ]
    name = ranks[0][1]
    for lv, title in ranks:
        if level >= lv:
            name = title
    return name


@router.message(Command("xp", "exp", "опыт"))
async def cmd_xp(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.reply("Команда работает в группе.")
        return
    user = message.from_user
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
    row = await get_xp(message.chat.id, user.id)
    if not row:
        await message.reply(f"У {mention(user)} пока нет опыта.")
        return
    await message.reply(
        f"⭐ {mention(user)}\n"
        f"Уровень: <b>{row['level']}</b> ({rank_name(row['level'])})\n"
        f"XP: <code>{row['xp']}</code>\n"
        f"Сообщений: <code>{row['messages']}</code>"
    )


@router.message(Command("rank", "ранг"))
async def cmd_rank(message: Message):
    row = await get_xp(message.chat.id, message.from_user.id)
    lvl = row["level"] if row else 1
    await message.reply(f"Твой ранг: <b>{rank_name(lvl)}</b> (ур. {lvl})")


@router.message(Command("toplevel", "xptop", "топ опыта"), IsGroupFilter())
async def cmd_top(message: Message):
    rows = await top_xp(message.chat.id, 10)
    if not rows:
        await message.reply("Пока пусто — пишите в чат.")
        return
    lines = ["🏆 <b>Топ активности</b>"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. <code>{r['user_id']}</code> — {r['xp']} XP, ур. {r['level']}")
    await message.reply("\n".join(lines))


@router.message(Command("setxp"), IsAdminFilter(), IsGroupFilter())
async def cmd_setxp(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user or not rest or not rest.strip().lstrip("-").isdigit():
        await message.reply("/setxp (ответ) 500")
        return
    lvl = await set_xp(message.chat.id, user.id, int(rest.strip()))
    await message.reply(f"XP {mention(user)} = {rest.strip()} (ур. {lvl})")


@router.message(Command("resetxp"), IsAdminFilter(), IsGroupFilter())
async def cmd_resetxp(message: Message, bot: Bot, command: CommandObject):
    if command.args and command.args.strip() == "all":
        await reset_xp(message.chat.id)
        await message.reply("Весь XP чата сброшен.")
        return
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Ответь на пользователя или /resetxp all")
        return
    await reset_xp(message.chat.id, user.id)
    await message.reply(f"XP {mention(user)} сброшен.")


@router.message(Command("xprate"), IsAdminFilter(), IsGroupFilter())
async def cmd_xprate(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        s = await get_settings(message.chat.id)
        await message.reply(f"Текущий XP за сообщение: {s.get('xp_amount', 8)}")
        return
    n = max(0, min(int(command.args.strip()), 100))
    await update_settings(message.chat.id, xp_amount=n, xp_enabled=1 if n else 0)
    await message.reply(f"XP за сообщение: {n}")


@router.message(Command("xpnotify"), IsAdminFilter(), IsGroupFilter())
async def cmd_xpnotify(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да", "yes")
    await update_settings(message.chat.id, xp_notify=1 if on else 0)
    await message.reply("Уведомления о уровне " + ("вкл" if on else "выкл"))


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def xp_listener(message: Message):
    if not message.from_user or message.from_user.is_bot:
        return
    if message.text and message.text.startswith("/"):
        return
    await ensure_chat(message.chat.id, message.chat.title)
    s = await get_settings(message.chat.id)
    if not s.get("xp_enabled", 1):
        return
    amount = int(s.get("xp_amount", 8) or 8)
    xp, level, up = await add_xp(message.chat.id, message.from_user.id, amount)
    if up and s.get("xp_notify", 0):
        try:
            await message.reply(
                f"🎉 {mention(message.from_user)} достиг уровня <b>{level}</b> ({rank_name(level)})!"
            )
        except Exception:
            pass
