"""
Command aliases & lightweight extras so catalog commands resolve.
Maps synonyms → existing behaviour; simple utils that need no extra state.
"""
from __future__ import annotations

import hashlib
import random
import re
import uuid
from datetime import datetime, timezone

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import card, ok, fail
from core.text import html_esc, mention

router = Router()

# ─── Simple synonym-only commands (informational redirect) ────────

SYNONYM_HELP = {
    "voiceban": "Закрой голосовые: <code>/lock voice</code>",
    "unvoiceban": "Открой: <code>/unlock voice</code>",
    "imgban": "Закрой медиа: <code>/lock photo</code>",
    "note": "Заметка: <code>/get имя</code> или <code>#имя</code>",
    "addnote": "Сохранить: <code>/save имя текст</code>",
    "rmnote": "Удалить: <code>/clear имя</code>",
    "trigger": "Автоответ: <code>/filter слово ответ</code>",
    "rmfilter": "Убрать: <code>/stop слово</code>",
    "warnsreset": "Синоним: <code>/resetwarns</code>",
    "promoterank": "Ранг: <code>/setrank @user N</code>",
    "demoterank": "Ранг: <code>/setrank @user N</code> · <code>/delrank</code>",
    "removecoins": "Монеты: <code>/addcoins @user -N</code>",
    "check": "См. <code>/info</code> · <code>/whoami</code>",
    "idcard": "См. <code>/id</code>",
    "admins": "См. <code>/adminlist</code>",
    "clean": "См. <code>/del</code> · <code>/purge</code>",
}


@router.message(Command(*SYNONYM_HELP.keys()))
async def cmd_synonym_hint(message: Message):
    raw = (message.text or "").lstrip("/")
    name = raw.split()[0].split("@")[0].lower()
    hint = SYNONYM_HELP.get(name)
    if hint:
        await message.reply(card("Подсказка", hint, emoji="💡"))
    else:
        await message.reply(fail("Команда не найдена. /commands"))


# ─── Working lightweight utils ────────────────────────────────────

@router.message(Command("uuid"))
async def cmd_uuid(message: Message):
    await message.reply(card("UUID", f"<code>{uuid.uuid4()}</code>", emoji="🧰"))


@router.message(Command("time"))
async def cmd_time(message: Message):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await message.reply(card("Время", f"UTC: <code>{now}</code>\nЛокаль сервера: <code>{local}</code>", emoji="🕐"))


@router.message(Command("color"))
async def cmd_color(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", arg or ""):
        await message.reply("Укажи hex: <code>/color FF5733</code>")
        return
    await message.reply(card("Цвет", f"#{arg.upper()}\nRGB: {int(arg[0:2],16)}, {int(arg[2:4],16)}, {int(arg[4:6],16)}", emoji="🎨"))


@router.message(Command("json"))
async def cmd_json(message: Message, command: CommandObject):
    import json
    raw = command.args or ""
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Пришли JSON: <code>/json {...}</code> или ответом")
        return
    try:
        data = json.loads(raw)
        pretty = json.dumps(data, ensure_ascii=False, indent=2)
        if len(pretty) > 3500:
            pretty = pretty[:3500] + "…"
        await message.reply(f"<pre>{html_esc(pretty)}</pre>")
    except Exception as e:
        await message.reply(fail(f"Невалидный JSON: {html_esc(e)}"))


@router.message(Command("code"))
async def cmd_code(message: Message, command: CommandObject):
    raw = command.args or ""
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/code print(1)</code>")
        return
    if len(raw) > 3500:
        raw = raw[:3500]
    await message.reply(f"<pre>{html_esc(raw)}</pre>")


@router.message(Command("poll"))
async def cmd_poll(message: Message, command: CommandObject):
    if message.chat.type == "private":
        await message.reply("Опросы создаются в группе.")
        return
    raw = (command.args or "").strip()
    # /poll Вопрос? | вариант1 | вариант2
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 3:
        await message.reply("Формат: <code>/poll Вопрос? | Да | Нет | Затрудняюсь</code>")
        return
    q, options = parts[0], parts[1:11]
    try:
        await message.answer_poll(question=q[:300], options=options, is_anonymous=False)
    except Exception as e:
        await message.reply(fail(f"Не удалось создать опрос: {html_esc(e)}"))


@router.message(Command("quiz"))
async def cmd_quiz(message: Message, command: CommandObject):
    if message.chat.type == "private":
        return
    raw = (command.args or "").strip()
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 3:
        await message.reply("Формат: <code>/quiz Вопрос? | верный | неверный1 | неверный2</code>\nПервый вариант после вопроса — правильный.")
        return
    q, options = parts[0], parts[1:11]
    try:
        await message.answer_poll(
            question=q[:300],
            options=options,
            type="quiz",
            correct_option_id=0,
            is_anonymous=False,
        )
    except Exception as e:
        await message.reply(fail(html_esc(str(e))))


@router.message(Command("8ball", "fortune"))
async def cmd_8ball(message: Message):
    answers = [
        "Бесспорно", "Предрешено", "Никаких сомнений", "Определённо да",
        "Можешь быть уверен", "Мне кажется — да", "Вероятнее всего", "Хорошие перспективы",
        "Знаки говорят — да", "Да", "Пока не ясно", "Спроси позже",
        "Лучше не рассказывать", "Сейчас нельзя предсказать", "Сконцентрируйся и спроси опять",
        "Даже не думай", "Мой ответ — нет", "По моим данным — нет", "Перспективы не очень", "Весьма сомнительно",
    ]
    await message.reply(card("Шар судьбы", f"🎱 <b>{random.choice(answers)}</b>", emoji="🔮"))


@router.message(Command("cat", "dog", "fox"))
async def cmd_animal(message: Message):
    name = (message.text or "").lstrip("/").split()[0].split("@")[0].lower()
    emoji = {"cat": "🐱", "dog": "🐶", "fox": "🦊"}.get(name, "🐾")
    await message.reply(f"{emoji} Случайный {name}! (открой Google/картинки — API картинок не подключён)")


@router.message(Command("compliment"))
async def cmd_compliment(message: Message):
    lines = [
        "Ты сегодня особенно крут.",
        "С тобой чат становится лучше.",
        "Твоя энергия заразительна.",
        "Ты заслуживаешь хороший день.",
        "Кто-то явно выспался и пришёл сиять.",
    ]
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.reply(f"💬 {mention(target)}, {random.choice(lines)}")


@router.message(Command("gay", "howgay", "iq", "pp", "love"))
async def cmd_meters(message: Message):
    name = (message.text or "").lstrip("/").split()[0].split("@")[0].lower()
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    seed = f"{target.id}:{name}"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    labels = {
        "gay": "🌈 Gay-метр",
        "howgay": "🌈 Gay-метр",
        "iq": "🧠 IQ",
        "pp": "📏 PP",
        "love": "❤️ Love",
    }
    await message.reply(card(labels.get(name, "Метр"), f"{mention(target)}\n<b>{val}%</b>", emoji="🎮"))


@router.message(Command("cuddle", "poke", "dance"))
async def cmd_actions_fun(message: Message):
    name = (message.text or "").lstrip("/").split()[0].split("@")[0].lower()
    target = message.reply_to_message.from_user if message.reply_to_message else None
    acts = {
        "cuddle": "прижимается к",
        "poke": "тыкает",
        "dance": "танцует с",
    }
    verb = acts.get(name, "взаимодействует с")
    if target:
        await message.reply(f"✨ {mention(message.from_user)} {verb} {mention(target)}")
    else:
        await message.reply(f"✨ {mention(message.from_user)} {verb}… воздух. Ответь на сообщение!")



@router.message(Command("timer"))
async def cmd_timer(message: Message, command: CommandObject):
    from core.timeparse import parse_time
    raw = (command.args or "").strip()
    if not raw:
        await message.reply("<code>/timer 5m текст</code>")
        return
    parts = raw.split(maxsplit=1)
    sec = parse_time(parts[0])
    note = parts[1] if len(parts) > 1 else "⏰ Время вышло!"
    if not sec or sec > 86400:
        await message.reply("Время: 10s / 5m / 1h (макс 24ч)")
        return
    await message.reply(ok(f"Таймер на {parts[0]} запущен…"))
    import asyncio
    await asyncio.sleep(sec)
    try:
        await message.reply(f"⏰ {html_esc(note)}")
    except Exception:
        pass
