"""New small working commands — TitanMod 4.9.3."""
from __future__ import annotations

import base64
import random
import time
from datetime import datetime, timezone

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject

from config import config
from core.style import card, ok, fail, HR
from core.text import html_esc, mention

router = Router()
_START_TS = time.monotonic()


@router.message(Command("uptime", "аптайм"))
async def cmd_uptime(message: Message):
    sec = int(time.monotonic() - _START_TS)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    await message.reply(
        card(
            "Аптайм",
            f"Процесс бота: <b>{h}ч {m}м {s}с</b>\n"
            f"Версия: <code>{config.VERSION}</code>",
            emoji="⏱",
        )
    )


@router.message(Command("chatid", "айдичата"))
async def cmd_chatid(message: Message):
    await message.reply(
        card(
            "ID чата",
            f"<code>{message.chat.id}</code>\nТип: {message.chat.type}",
            emoji="🆔",
        )
    )


@router.message(Command("userid", "айди"))
async def cmd_userid(message: Message, command: CommandObject):
    u = message.from_user
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
    elif command.args and command.args.strip().lstrip("-").isdigit():
        await message.reply(card("ID", f"<code>{command.args.strip()}</code>", emoji="🆔"))
        return
    if not u:
        return
    await message.reply(
        card(
            "ID пользователя",
            f"{mention(u)}\n<code>{u.id}</code>",
            emoji="🆔",
        )
    )


@router.message(Command("b64", "base64"))
async def cmd_b64(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message:
        raw = (message.reply_to_message.text or "").strip()
    if not raw:
        await message.reply("<code>/b64 encode текст</code>\n<code>/b64 decode ...</code>")
        return
    parts = raw.split(maxsplit=1)
    mode = parts[0].lower()
    text = parts[1] if len(parts) > 1 else ""
    if mode in ("encode", "enc", "e") and text:
        out = base64.b64encode(text.encode("utf-8")).decode("ascii")
        await message.reply(card("Base64", f"<code>{html_esc(out[:3500])}</code>", emoji="🔐"))
        return
    if mode in ("decode", "dec", "d") and text:
        try:
            out = base64.b64decode(text.encode("ascii"), validate=False).decode("utf-8", errors="replace")
            await message.reply(card("Base64 decode", html_esc(out[:3500]), emoji="🔐"))
        except Exception:
            await message.reply(fail("Не удалось декодировать"))
        return
    # default encode whole args
    out = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    await message.reply(card("Base64", f"<code>{html_esc(out[:3500])}</code>", emoji="🔐"))


@router.message(Command("ship", "шип"))
async def cmd_ship(message: Message, command: CommandObject):
    a = message.from_user
    b = message.reply_to_message.from_user if message.reply_to_message else None
    args = (command.args or "").strip()
    if not b and args:
        await message.reply(fail("Ответь на сообщение второго человека: /ship"))
        return
    if not b:
        await message.reply(fail("Ответь на сообщение: <code>/ship</code>"))
        return
    if not a:
        return
    seed = f"{min(a.id,b.id)}:{max(a.id,b.id)}"
    pct = int(abs(hash(seed)) % 101)
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    await message.reply(
        card(
            "Ship",
            f"{mention(a)} + {mention(b)}\n"
            f"<b>{pct}%</b>\n{bar}",
            emoji="💘",
        )
    )


@router.message(Command("percent", "шанс"))
async def cmd_percent(message: Message, command: CommandObject):
    q = (command.args or "это").strip()[:120]
    pct = random.randint(0, 100)
    await message.reply(
        card("Шанс", f"{html_esc(q)}\n<b>{pct}%</b>", emoji="📊")
    )


@router.message(Command("pick", "рандомвыбор"))
async def cmd_pick(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw:
        await message.reply("<code>/pick а | б | в</code>")
        return
    parts = [p.strip() for p in raw.replace(",", "|").split("|") if p.strip()]
    if len(parts) < 2:
        await message.reply(fail("Нужно минимум 2 варианта через |"))
        return
    await message.reply(card("Выбор", f"→ <b>{html_esc(random.choice(parts))}</b>", emoji="🎯"))


@router.message(Command("when", "когда"))
async def cmd_when(message: Message, command: CommandObject):
    q = (command.args or "это").strip()[:100]
    days = random.randint(0, 365)
    await message.reply(
        card(
            "Когда?",
            f"{html_esc(q)}\nЧерез <b>{days}</b> дн. (шутка, не предсказание)",
            emoji="📅",
        )
    )


@router.message(Command("emojirand", "эмодзи"))
async def cmd_emoji(message: Message):
    pool = list("😀😁😂🤣😃😄😅😆😉😊😋😎😍🥳🤔😏😐😑😶🙄😮😯😴🥺😢😭😤😠🤡👻😺")
    await message.reply(card("Эмодзи", random.choice(pool) * random.randint(1, 5), emoji="✨"))


@router.callback_query(F.data.startswith("game:hint:"))
async def game_hint_cb(callback: CallbackQuery):
    key = (callback.data or "").split(":")[-1]
    hints = {
        "rps": "✂️ <b>КНБ</b>\n<code>/rps камень</code> · <code>/rps ножницы</code> · <code>/rps бумага</code>",
        "guess": "🔢 <b>Число</b>\n<code>/guess new</code> затем <code>/guess 50</code>",
        "hangman": "🪢 <b>Виселица</b>\n<code>/hangman new</code> · <code>/hangman а</code>",
        "bj": "🃏 <b>21</b>\n<code>/bj new</code> · <code>/bj hit</code> · <code>/bj stand</code>",
        "article": "📜 <b>Статья РФ</b>\n<code>/статья 19</code> · <code>/статьи</code>",
    }
    text = hints.get(key, "См. <code>/minigames</code>")
    try:
        await callback.message.answer(text)
    except Exception:
        pass
    try:
        await callback.answer()
    except Exception:
        pass
