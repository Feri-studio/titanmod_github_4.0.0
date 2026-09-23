import base64
import hashlib
import random
import re
import time
import ast
import operator
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsGroupFilter
from core.text import mention, html_esc
from core.timeparse import parse_time, format_time
from database.db import (
    set_afk, get_afk, clear_afk, change_rep, last_rep_time, top_rep, get_settings,
    add_reminder, list_reminders, delete_reminder, get_user,
)
from handlers.common import resolve_user
from config import config

router = Router()
STARTED = time.time()

RU = "йцукенгшщзхъфывапролджэячсмитьбю.ё"
EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
MAP_RU2EN = str.maketrans(RU + RU.upper(), EN + EN.upper())
MAP_EN2RU = str.maketrans(EN + EN.upper(), RU + RU.upper())

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("bad expr")


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    t = time.time()
    msg = await message.reply("pong")
    ms = int((time.time() - t) * 1000)
    await msg.edit_text(f"pong {ms}ms")


@router.message(Command("uptime"))
async def cmd_uptime(message: Message):
    await message.reply(f"Аптайм: {format_time(int(time.time() - STARTED))}\nВерсия {config.VERSION}")


@router.message(Command("afk"))
async def cmd_afk(message: Message, command: CommandObject):
    s = await get_settings(message.chat.id) if message.chat.type != "private" else {}
    if s and not s.get("afk_enabled", 1):
        return
    reason = command.args or "AFK"
    await set_afk(message.from_user.id, reason)
    await message.reply(f"{mention(message.from_user)} теперь AFK: {html_esc(reason)}")


@router.message(Command("remind"))
async def cmd_remind(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/remind 1h текст")
        return
    parts = command.args.split(maxsplit=1)
    sec = parse_time(parts[0], 0)
    if sec <= 0:
        await message.reply("Не понял время.")
        return
    text = parts[1] if len(parts) > 1 else "Напоминание"
    rid = await add_reminder(message.chat.id, message.from_user.id, text, time.time() + sec)
    await message.reply(f"Ок, напомню через {format_time(sec)} (#{rid})")


@router.message(Command("reminders"))
async def cmd_reminders(message: Message):
    rows = await list_reminders(message.from_user.id)
    if not rows:
        await message.reply("Нет напоминаний.")
        return
    lines = []
    for r in rows:
        left = int(r["fire_at"] - time.time())
        lines.append(f"#{r['id']} через {format_time(max(left, 0))}: {html_esc(r['text'])}")
    await message.reply("\n".join(lines))


@router.message(Command("forget"))
async def cmd_forget(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/forget id")
        return
    ok = await delete_reminder(int(command.args.strip()), message.from_user.id)
    await message.reply("Удалено." if ok else "Не найдено.")


@router.message(Command("calc"))
async def cmd_calc(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/calc 2+2*2")
        return
    try:
        tree = ast.parse(command.args.replace("^", "**"), mode="eval")
        val = _safe_eval(tree)
        await message.reply(f"= {val}")
    except Exception:
        await message.reply("Не могу посчитать.")


@router.message(Command("b64e"))
async def cmd_b64e(message: Message, command: CommandObject):
    if not command.args:
        return
    await message.reply(html_esc(base64.b64encode(command.args.encode()).decode()))


@router.message(Command("b64d"))
async def cmd_b64d(message: Message, command: CommandObject):
    if not command.args:
        return
    try:
        await message.reply(html_esc(base64.b64decode(command.args.encode()).decode()))
    except Exception:
        await message.reply("Невалидный base64")


@router.message(Command("hash"))
async def cmd_hash(message: Message, command: CommandObject):
    if not command.args:
        return
    raw = command.args.encode()
    await message.reply(f"md5 <code>{hashlib.md5(raw).hexdigest()}</code>\nsha256 <code>{hashlib.sha256(raw).hexdigest()}</code>")


@router.message(Command("password"))
async def cmd_pass(message: Message, command: CommandObject):
    n = 16
    if command.args and command.args.strip().isdigit():
        n = max(6, min(64, int(command.args.strip())))
    alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*"
    pwd = "".join(random.choice(alphabet) for _ in range(n))
    await message.reply(f"<code>{html_esc(pwd)}</code>")


@router.message(Command("say"), IsGroupFilter())
async def cmd_say(message: Message, command: CommandObject):
    if not command.args:
        return
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer(command.args)


@router.message(Command("tr"))
async def cmd_tr(message: Message, command: CommandObject):
    t = command.args or (message.reply_to_message.text if message.reply_to_message else "")
    if not t:
        return
    ru_chars = sum(1 for c in t.lower() if c in RU)
    mapped = t.translate(MAP_RU2EN if ru_chars >= len(t) / 4 else MAP_EN2RU)
    await message.reply(html_esc(mapped))
