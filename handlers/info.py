from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.style import HR
from core.text import mention, html_esc, user_title
from core.permissions import display_status
from database.db import (
    get_warns_count, get_punishments, get_name_history, get_user_notes, add_user_note,
    get_stats, get_user, get_settings, is_gbanned, get_chat_fed, is_fbanned, is_approved,
)
from handlers.common import resolve_user
from datetime import datetime

router = Router()


@router.message(Command("id"))
async def cmd_id(message: Message):
    parts = [f"Чат: <code>{message.chat.id}</code>"]
    if message.from_user:
        parts.append(f"Ты: <code>{message.from_user.id}</code>")
    if message.reply_to_message and message.reply_to_message.from_user:
        parts.append(f"Reply: <code>{message.reply_to_message.from_user.id}</code>")
    src = message.reply_to_message or message
    if src.photo:
        parts.append(f"photo file_id: <code>{src.photo[-1].file_id}</code>")
    if src.sticker:
        parts.append(f"sticker: <code>{src.sticker.file_id}</code> unique <code>{src.sticker.file_unique_id}</code>")
    if src.document:
        parts.append(f"doc: <code>{src.document.file_id}</code>")
    await message.reply("\n".join(parts))


@router.message(Command("info", "whois", "uinfo"))
async def cmd_info(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    warns = await get_warns_count(message.chat.id, user.id) if message.chat.type != "private" else 0
    try:
        member = await bot.get_chat_member(message.chat.id, user.id)
        status = display_status(member.status)
    except Exception:
        status = "—"
    db = await get_user(user.id)
    g = await is_gbanned(user.id)
    fed = await get_chat_fed(message.chat.id) if message.chat.type != "private" else None
    fb = await is_fbanned(fed["fed_id"], user.id) if fed else None
    appr = await is_approved(message.chat.id, user.id) if message.chat.type != "private" else False
    text = (
        f"👤 <b>Профиль</b>\n"
        f"{HR}\n"
        f"{mention(user)}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: @{html_esc(user.username) if user.username else 'нет'}\n"
        f"Статус: {status}\n"
        f"Варны: <b>{warns}</b>\n"
        f"Репутация: {(db or {}).get('reputation', 0)}\n"
        f"Approved: {'✅' if appr else '—'}\n"
        f"Gban: {html_esc(g['reason']) if g else '—'}\n"
        f"Fban: {html_esc(fb['reason']) if fb else '—'}"
    )
    await message.reply(text)


@router.message(Command("ginfo"), IsGroupFilter())
async def cmd_ginfo(message: Message, bot: Bot):
    chat = message.chat
    try:
        count = await bot.get_chat_member_count(chat.id)
    except Exception:
        count = "?"
    s = await get_settings(chat.id)
    await message.reply(
        f"<b>{html_esc(chat.title)}</b>\n"
        f"ID: <code>{chat.id}</code>\n"
        f"Тип: {chat.type}\n"
        f"Username: @{chat.username or 'нет'}\n"
        f"Участников: {count}\n"
        f"Лимит варнов: {s.get('warn_limit')}\n"
        f"Антифлуд: {s.get('flood_limit')}/{s.get('flood_period')}\n"
        f"Капча: {s.get('welcome_captcha')}"
    )


@router.message(Command("history"), IsAdminFilter())
async def cmd_history(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    rows = await get_name_history(user.id)
    if not rows:
        await message.reply("Истории нет.")
        return
    lines = [f"История {mention(user)}:"]
    for r in rows:
        lines.append(f"• {html_esc(r.get('name'))} @{html_esc(r.get('username') or '—')} ({r.get('created_at')})")
    await message.reply("\n".join(lines))


@router.message(Command("punishments"), IsAdminFilter())
async def cmd_pun(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    rows = await get_punishments(message.chat.id, user.id)
    if not rows:
        await message.reply("История наказаний пуста.")
        return
    lines = [f"Наказания {mention(user)}:"]
    for r in rows[:20]:
        lines.append(f"• {r['type']} — {html_esc(r.get('reason') or '')} ({str(r.get('created_at'))[:16]})")
    await message.reply("\n".join(lines))


@router.message(Command("usernote"), IsAdminFilter(), IsGroupFilter())
async def cmd_usernote(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user or not rest:
        await message.reply("/usernote (ответ) текст")
        return
    await add_user_note(message.chat.id, user.id, message.from_user.id, rest)
    await message.reply("Заметка сохранена.")


@router.message(Command("noteson"), IsAdminFilter(), IsGroupFilter())
async def cmd_noteson(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    rows = await get_user_notes(message.chat.id, user.id)
    if not rows:
        await message.reply("Нет заметок.")
        return
    lines = [f"Заметки на {mention(user)}:"]
    for r in rows:
        lines.append(f"• {html_esc(r['note'])} ({r['created_at']})")
    await message.reply("\n".join(lines))


@router.message(Command("stats"), IsGroupFilter())
async def cmd_stats(message: Message):
    rows = await get_stats(message.chat.id, 14)
    if not rows:
        await message.reply("Статистики пока нет.")
        return
    tot = {"messages": 0, "joins": 0, "leaves": 0, "bans": 0, "warns": 0, "mutes": 0, "kicks": 0, "deleted": 0}
    lines = ["Статистика:"]
    for r in rows:
        for k in tot:
            tot[k] += r.get(k) or 0
        lines.append(f"{r['date']}: {r['messages']} msg, {r['joins']} join, {r['bans']} ban")
    lines.append(
        "Итого: " + ", ".join(f"{k}={v}" for k, v in tot.items())
    )
    await message.reply("\n".join(lines))


@router.message(Command("bots"), IsGroupFilter())
async def cmd_bots(message: Message, bot: Bot):
    admins = await bot.get_chat_administrators(message.chat.id)
    bots = [a for a in admins if a.user.is_bot]
    await message.reply("Боты-админы:\n" + "\n".join(mention(a.user) for a in bots) or "нет")


@router.message(Command("zombies"), IsAdminFilter(), IsGroupFilter())
async def cmd_zombies(message: Message):
    await message.reply("Полный скан удалённых аккаунтов Telegram API не отдаёт списком участников. Кикай вручную по сообщениям Deleted Account.")
