"""Rank hierarchy commands — TitanMod 4.0."""
from __future__ import annotations

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import config
from core.ranks import (
    get_rank_info, rank_badge, rank_list_text, RANKS, RANK_BY_KEY, COMMAND_PERMS,
)
from core.style import HR, HR_LIGHT, card, ok, fail, rank_card, safe_edit, safe_answer
from core.text import html_esc, mention
from core.permissions import admin_cache
from database.extra import get_user_rank, set_user_rank, list_ranks, get_rank_row, clear_user_rank
from handlers.common import resolve_user

router = Router()


async def effective_rank(bot: Bot, chat_id: int, user_id: int) -> int:
    """Highest of: stored rank, Telegram admin status, bot owner."""
    if config.is_owner(user_id):
        return 7
    stored = await get_user_rank(chat_id, user_id)
    if await admin_cache.is_creator(bot, chat_id, user_id):
        return max(stored, 7)
    if await admin_cache.is_admin(bot, chat_id, user_id):
        return max(stored, 5)
    return stored


async def has_perm(bot: Bot, chat_id: int, user_id: int, perm: str) -> bool:
    level = await effective_rank(bot, chat_id, user_id)
    info = get_rank_info(level)
    return info.has(perm)


def ranks_kb() -> object:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📋 Список рангов", callback_data="ranks:list"))
    b.row(InlineKeyboardButton(text="❓ Как работает", callback_data="ranks:help"))
    return b.as_markup()


@router.message(Command("ranks", "ранги", "hierarchy"))
async def cmd_ranks(message: Message):
    text = card(
        "Система рангов",
        rank_list_text("ru")
        + f"\n{HR_LIGHT}\n"
        + "Назначить: <code>/setrank @user 3</code> или <code>/setrank @user moderator</code>\n"
        + "Снять: <code>/delrank @user</code>\n"
        + "Мой ранг: <code>/myrank</code>",
        footer="TitanMod Hierarchy · 8 уровней",
        emoji="🏅",
    )
    await message.reply(text, reply_markup=ranks_kb())


@router.message(Command("myrank", "мойранг"))
async def cmd_myrank(message: Message, bot: Bot):
    chat_id = message.chat.id
    if message.chat.type == "private":
        await message.reply("ℹ️ Эта команда работает в группе. В ЛС открой /menu")
        return
    user = message.from_user
    level = await effective_rank(bot, chat_id, user.id)
    info = get_rank_info(level)
    row = await get_rank_row(chat_id, user.id)
    custom = (row or {}).get("custom_title") or ""
    extra = f"\n▸ Титул: <i>{html_esc(custom)}</i>" if custom else ""
    text = (
        f"🏅 <b>Твой ранг</b>\n{HR}\n"
        f"👤 {mention(user)}\n"
        f"▸ {info.emoji} <b>{info.name}</b> <code>[{level}]</code>{extra}\n"
        f"{HR_LIGHT}\n"
        f"Права: <code>{', '.join(sorted(info.perms)[:12]) or '—'}</code>"
    )
    await message.reply(text)


@router.message(Command("setrank", "rankset", "setstaff"))
async def cmd_setrank(message: Message, command: CommandObject, bot: Bot):
    if message.chat.type == "private":
        await message.reply("❌ Только в группе")
        return
    actor_level = await effective_rank(bot, message.chat.id, message.from_user.id)
    if actor_level < 5 and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нужен ранг Админ или выше"))
        return

    args_str = (command.args or "") if command else ""
    target, rest = await resolve_user(message, bot, args_str)
    if not target:
        await message.reply(
            "Укажи пользователя <b>ответом</b> на сообщение или числовым id:\n"
            "<code>/setrank 123456789 3</code>\n"
            "<code>/setrank 123456789 moderator</code>"
        )
        return

    args = (rest or "").strip().split()
    if not args:
        await message.reply(
            "Укажи уровень (0–7) или ключ:\n"
            "<code>member trusted helper moderator senior admin head owner</code>"
        )
        return

    raw = args[0].lower()
    if raw.isdigit():
        level = int(raw)
    elif raw in RANK_BY_KEY:
        level = RANK_BY_KEY[raw]
    else:
        await message.reply(fail("Неизвестный ранг. Используй 0-7 или ключ."))
        return

    level = max(0, min(7, level))
    if level >= actor_level and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нельзя назначить ранг ≥ своего"))
        return

    target_current = await effective_rank(bot, message.chat.id, target.id)
    if target_current >= actor_level and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нельзя менять ранг того, кто ≥ тебя"))
        return

    custom = " ".join(args[1:]) if len(args) > 1 else None
    await set_user_rank(message.chat.id, target.id, level, message.from_user.id, custom)
    info = get_rank_info(level)
    text = rank_card(mention(target), f"{info.emoji} {info.name}", level,
                     extra=f"🛡 Назначил: {mention(message.from_user)}")
    await message.reply(text)


@router.message(Command("delrank", "removerank", "unrank"))
async def cmd_delrank(message: Message, command: CommandObject, bot: Bot):
    if message.chat.type == "private":
        return
    actor_level = await effective_rank(bot, message.chat.id, message.from_user.id)
    if actor_level < 5:
        await message.reply(fail("Нужен ранг Админ+"))
        return
    args_str = (command.args or "") if command else ""
    target, _ = await resolve_user(message, bot, args_str)
    if not target:
        await message.reply("Укажи пользователя ответом или id")
        return
    target_level = await get_user_rank(message.chat.id, target.id)
    if target_level >= actor_level and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нельзя снять ранг ≥ своего"))
        return
    await clear_user_rank(message.chat.id, target.id)
    await message.reply(ok(f"Ранг {mention(target)} сброшен до Участника"))


@router.message(Command("stafflist", "modlist", "rankstaff"))
async def cmd_staff(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.reply("Только в группе")
        return
    rows = await list_ranks(message.chat.id, min_level=1)
    if not rows:
        await message.reply("📋 Штат пуст. Назначь через <code>/setrank</code>")
        return
    lines = [f"🏅 <b>Штат чата</b>", HR]
    for r in rows:
        info = get_rank_info(r["rank_level"])
        uid = r["user_id"]
        title = r.get("custom_title") or ""
        extra = f" — <i>{html_esc(title)}</i>" if title else ""
        lines.append(f"{info.emoji} <code>{uid}</code> · {info.name}{extra}")
    lines.append(HR_LIGHT)
    lines.append(f"Всего: <b>{len(rows)}</b>")
    await message.reply("\n".join(lines))


@router.callback_query(F.data.startswith("ranks:"))
async def ranks_cb(callback: CallbackQuery):
    action = callback.data.split(":", 1)[1]
    if action == "list":
        text = card("Иерархия", rank_list_text("ru"), emoji="🏅")
        await safe_edit(callback.message, text, ranks_kb())
    elif action == "help":
        text = card(
            "Как работают ранги",
            "• Ранги хранятся в базе бота и работают вместе с правами Telegram\n"
            "• Владелец чата (creator) и владельцы бота всегда = 👑 Owner\n"
            "• Telegram-админы автоматически получают минимум уровень Admin\n"
            "• Назначение: <code>/setrank @user moderator</code>\n"
            "• Список штата: <code>/staff</code>\n"
            "• Каждый ранг открывает свой набор прав (варны, баны, настройки…)",
            emoji="❓",
        )
        await safe_edit(callback.message, text, ranks_kb())
    await safe_answer(callback)
