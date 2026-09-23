"""Chat statistics and quick diagnostics — TitanMod 4.5.9."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import config
from core.style import card, HR, HR_LIGHT, ok, fail
from core.text import html_esc, mention
from database.db import get_stats, get_settings, count_chats
from filters.admin import IsGroupFilter

router = Router()


@router.message(Command("chatstats", "стата", "chatstat"))
async def cmd_chatstats(message: Message):
    if message.chat.type == "private":
        await message.reply("Команда для группы: /chatstats")
        return
    rows = await get_stats(message.chat.id, days=7)
    if not rows:
        await message.reply(
            card(
                "Статистика чата",
                "Пока пусто. Данные появятся после активности\n"
                "(сообщения, баны, варны, входы).",
                emoji="📊",
                footer="окно: 7 дней",
            )
        )
        return
    tot = {
        "messages": 0, "joins": 0, "leaves": 0, "warns": 0,
        "bans": 0, "mutes": 0, "kicks": 0, "deleted": 0,
    }
    for r in rows:
        for k in tot:
            tot[k] += int(r.get(k) or 0)
    body = "\n".join(
        [
            f"<b>{html_esc(message.chat.title or 'чат')}</b> · 7 дней",
            HR_LIGHT,
            f"› Сообщения: <b>{tot['messages']}</b>",
            f"› Входы / выходы: <b>{tot['joins']}</b> / <b>{tot['leaves']}</b>",
            f"› Варны: <b>{tot['warns']}</b>",
            f"› Баны / кики: <b>{tot['bans']}</b> / <b>{tot['kicks']}</b>",
            f"› Муты: <b>{tot['mutes']}</b>",
            f"› Удалено автомодом: <b>{tot['deleted']}</b>",
        ]
    )
    await message.reply(card("Статистика", body, emoji="📊", footer="TitanMod · /chatstats"))


@router.message(Command("whoami", "я"))
async def cmd_whoami(message: Message, bot: Bot):
    u = message.from_user
    if not u:
        return
    lines = [
        f"› Имя: <b>{html_esc(u.full_name)}</b>",
        f"› ID: <code>{u.id}</code>",
        f"› Username: @{html_esc(u.username or '—')}",
        f"› Чат: <code>{message.chat.id}</code> ({message.chat.type})",
    ]
    if message.chat.type in ("group", "supergroup"):
        try:
            from core.ranks import effective_rank, get_rank_info
            lvl = await effective_rank(bot, message.chat.id, u.id)
            info = get_rank_info(lvl)
            lines.append(f"› Ранг бота: {info.emoji} <b>{info.name}</b> ({lvl})")
        except Exception:
            pass
        try:
            s = await get_settings(message.chat.id)
            lines.append(
                f"› Группа активирована: "
                f"<b>{'да' if s.get('group_activated') in (1, True, '1', 'on') else 'нет'}</b>"
            )
        except Exception:
            pass
    await message.reply(card("Кто я", "\n".join(lines), emoji="🪪"))


@router.message(Command("botinfo", "о_боте"))
async def cmd_botinfo(message: Message):
    try:
        n = await count_chats()
    except Exception:
        n = "?"
    await message.reply(
        card(
            config.BOT_NAME,
            "\n".join(
                [
                    f"› Версия: <code>{config.VERSION}</code>",
                    f"› Чатов в БД: <b>{n}</b>",
                    f"› Владельцев: <b>{len(config.ADMINS)}</b>",
                    f"› Каталог: <code>/commands</code>",
                    f"› Кабинет: <code>/menu</code>",
                    f"› Панель: uvicorn panel.main:app",
                ]
            ),
            emoji="✨",
            footer="TitanMod",
        )
    )
