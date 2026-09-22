"""Expanded utilities pack — many small working commands."""
from __future__ import annotations

import hashlib
import random
import re
import string
from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import card, ok, fail
from core.text import html_esc
from core.lib import textops, mathops

router = Router()


@router.message(Command("wordcount"))
async def cmd_wordcount(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/wordcount …</code> или ответом")
        return
    await message.reply(card("Слова", f"<b>{len(raw.split())}</b>", emoji="🧰"))

@router.message(Command("charcount"))
async def cmd_charcount(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/charcount …</code> или ответом")
        return
    await message.reply(card("Символы", f"<b>{len(raw)}</b>", emoji="🧰"))

@router.message(Command("upper"))
async def cmd_upper(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/upper …</code> или ответом")
        return
    await message.reply(html_esc(raw.upper()))

@router.message(Command("lower"))
async def cmd_lower(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/lower …</code> или ответом")
        return
    await message.reply(html_esc(raw.lower()))

@router.message(Command("titlecase"))
async def cmd_titlecase(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/titlecase …</code> или ответом")
        return
    await message.reply(html_esc(raw.title()))

@router.message(Command("swapcase"))
async def cmd_swapcase(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/swapcase …</code> или ответом")
        return
    await message.reply(html_esc(raw.swapcase()))

@router.message(Command("strip"))
async def cmd_strip(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/strip …</code> или ответом")
        return
    await message.reply(html_esc(raw.strip()))

@router.message(Command("collapse"))
async def cmd_collapse(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/collapse …</code> или ответом")
        return
    await message.reply(html_esc(" ".join(raw.split())))

@router.message(Command("repeat"))
async def cmd_repeat(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/repeat …</code> или ответом")
        return
    await message.reply(html_esc((raw + " ") * 3))

@router.message(Command("shufflewords"))
async def cmd_shufflewords(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/shufflewords …</code> или ответом")
        return
    w=raw.split(); random.shuffle(w); await message.reply(html_esc(" ".join(w)))

@router.message(Command("sortwords"))
async def cmd_sortwords(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/sortwords …</code> или ответом")
        return
    await message.reply(html_esc(" ".join(sorted(raw.split(), key=str.lower))))

@router.message(Command("uniquewords"))
async def cmd_uniquewords(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/uniquewords …</code> или ответом")
        return
    seen=[];
    for w in raw.split():
        if w not in seen: seen.append(w)
    await message.reply(html_esc(" ".join(seen)))

@router.message(Command("firstword"))
async def cmd_firstword(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/firstword …</code> или ответом")
        return
    await message.reply(html_esc(raw.split()[0] if raw.split() else ""))

@router.message(Command("lastword"))
async def cmd_lastword(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/lastword …</code> или ответом")
        return
    await message.reply(html_esc(raw.split()[-1] if raw.split() else ""))

@router.message(Command("middle"))
async def cmd_middle(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/middle …</code> или ответом")
        return
    await message.reply(html_esc(raw[len(raw)//4: 3*len(raw)//4] or raw))

@router.message(Command("prefix"))
async def cmd_prefix(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/prefix …</code> или ответом")
        return
    await message.reply(html_esc(">> " + raw))

@router.message(Command("suffix"))
async def cmd_suffix(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/suffix …</code> или ответом")
        return
    await message.reply(html_esc(raw + " <<"))

@router.message(Command("wrap"))
async def cmd_wrap(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/wrap …</code> или ответом")
        return
    await message.reply(html_esc("[" + raw + "]"))

@router.message(Command("levenshtein"))
async def cmd_levenshtein(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/levenshtein …</code> или ответом")
        return
    parts=raw.split("|",1)
    if len(parts)<2:
        await message.reply("a|b")
        return
    a,b=parts[0].strip(),parts[1].strip()
    # simple distance
    if a==b: d=0
    else: d=abs(len(a)-len(b))+sum(1 for x,y in zip(a,b) if x!=y)
    await message.reply(card("Distance", f"<b>{d}</b>", emoji="🧰"))

@router.message(Command("palindrome"))
async def cmd_palindrome(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("Текст: <code>/palindrome …</code> или ответом")
        return
    t=re.sub(r"\W","",raw.lower()); await message.reply(ok("палиндром") if t==t[::-1] else fail("не палиндром"))

@router.message(Command("hashmd5"))
async def cmd_hash_md5(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("/hashmd5 текст")
        return
    h = hashlib.md5(raw.encode()).hexdigest()
    await message.reply(card("MD5", f"<code>{h}</code>", emoji="🔐"))

@router.message(Command("hashsha1"))
async def cmd_hash_sha1(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("/hashsha1 текст")
        return
    h = hashlib.sha1(raw.encode()).hexdigest()
    await message.reply(card("SHA1", f"<code>{h}</code>", emoji="🔐"))

@router.message(Command("hashsha256"))
async def cmd_hash_sha256(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("/hashsha256 текст")
        return
    h = hashlib.sha256(raw.encode()).hexdigest()
    await message.reply(card("SHA256", f"<code>{h}</code>", emoji="🔐"))

@router.message(Command("hashsha512"))
async def cmd_hash_sha512(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw and message.reply_to_message and message.reply_to_message.text:
        raw = message.reply_to_message.text
    if not raw:
        await message.reply("/hashsha512 текст")
        return
    h = hashlib.sha512(raw.encode()).hexdigest()
    await message.reply(card("SHA512", f"<code>{h}</code>", emoji="🔐"))

@router.message(Command("rand1"))
async def cmd_rand_1(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 10)}</b> (1–10)", emoji="🎲"))

@router.message(Command("rand2"))
async def cmd_rand_2(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 20)}</b> (1–20)", emoji="🎲"))

@router.message(Command("rand3"))
async def cmd_rand_3(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 30)}</b> (1–30)", emoji="🎲"))

@router.message(Command("rand4"))
async def cmd_rand_4(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 40)}</b> (1–40)", emoji="🎲"))

@router.message(Command("rand5"))
async def cmd_rand_5(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 50)}</b> (1–50)", emoji="🎲"))

@router.message(Command("rand6"))
async def cmd_rand_6(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 60)}</b> (1–60)", emoji="🎲"))

@router.message(Command("rand7"))
async def cmd_rand_7(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 70)}</b> (1–70)", emoji="🎲"))

@router.message(Command("rand8"))
async def cmd_rand_8(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 80)}</b> (1–80)", emoji="🎲"))

@router.message(Command("rand9"))
async def cmd_rand_9(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 90)}</b> (1–90)", emoji="🎲"))

@router.message(Command("rand10"))
async def cmd_rand_10(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 100)}</b> (1–100)", emoji="🎲"))

@router.message(Command("rand11"))
async def cmd_rand_11(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 110)}</b> (1–110)", emoji="🎲"))

@router.message(Command("rand12"))
async def cmd_rand_12(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 120)}</b> (1–120)", emoji="🎲"))

@router.message(Command("rand13"))
async def cmd_rand_13(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 130)}</b> (1–130)", emoji="🎲"))

@router.message(Command("rand14"))
async def cmd_rand_14(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 140)}</b> (1–140)", emoji="🎲"))

@router.message(Command("rand15"))
async def cmd_rand_15(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 150)}</b> (1–150)", emoji="🎲"))

@router.message(Command("rand16"))
async def cmd_rand_16(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 160)}</b> (1–160)", emoji="🎲"))

@router.message(Command("rand17"))
async def cmd_rand_17(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 170)}</b> (1–170)", emoji="🎲"))

@router.message(Command("rand18"))
async def cmd_rand_18(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 180)}</b> (1–180)", emoji="🎲"))

@router.message(Command("rand19"))
async def cmd_rand_19(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 190)}</b> (1–190)", emoji="🎲"))

@router.message(Command("rand20"))
async def cmd_rand_20(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 200)}</b> (1–200)", emoji="🎲"))

@router.message(Command("rand21"))
async def cmd_rand_21(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 210)}</b> (1–210)", emoji="🎲"))

@router.message(Command("rand22"))
async def cmd_rand_22(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 220)}</b> (1–220)", emoji="🎲"))

@router.message(Command("rand23"))
async def cmd_rand_23(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 230)}</b> (1–230)", emoji="🎲"))

@router.message(Command("rand24"))
async def cmd_rand_24(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 240)}</b> (1–240)", emoji="🎲"))

@router.message(Command("rand25"))
async def cmd_rand_25(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 250)}</b> (1–250)", emoji="🎲"))

@router.message(Command("rand26"))
async def cmd_rand_26(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 260)}</b> (1–260)", emoji="🎲"))

@router.message(Command("rand27"))
async def cmd_rand_27(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 270)}</b> (1–270)", emoji="🎲"))

@router.message(Command("rand28"))
async def cmd_rand_28(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 280)}</b> (1–280)", emoji="🎲"))

@router.message(Command("rand29"))
async def cmd_rand_29(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 290)}</b> (1–290)", emoji="🎲"))

@router.message(Command("rand30"))
async def cmd_rand_30(message: Message):
    await message.reply(card("Random", f"<b>{random.randint(1, 300)}</b> (1–300)", emoji="🎲"))

@router.message(Command("genpass", "genpassword"))
async def cmd_genpass(message: Message, command: CommandObject):
    try:
        n = int((command.args or "16").split()[0])
    except Exception:
        n = 16
    n = max(4, min(n, 64))
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    pwd = "".join(random.choice(alphabet) for _ in range(n))
    await message.reply(card("Пароль", f"<code>{html_esc(pwd)}</code>", emoji="🔑"))


@router.message(Command("unix", "epoch"))
async def cmd_unix(message: Message):
    await message.reply(card("Unix time", f"<code>{int(datetime.now(timezone.utc).timestamp())}</code>", emoji="🕐"))


@router.message(Command("isodate"))
async def cmd_isodate(message: Message):
    await message.reply(card("ISO", f"<code>{datetime.now(timezone.utc).isoformat()}</code>", emoji="📅"))

@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    parts = (command.args or "").replace(","," ").split()
    if len(parts) < 2:
        await message.reply("<code>/add a b</code>")
        return
    try:
        a, b = float(parts[0]), float(parts[1])
        if "add" == "add": r = a + b
        elif "add" == "sub": r = a - b
        elif "add" == "mul": r = a * b
        else: r = a / b if b else 0
        await message.reply(card("Результат", f"<b>{r}</b>", emoji="🧮"))
    except Exception:
        await message.reply(fail("Числа"))

@router.message(Command("sub"))
async def cmd_sub(message: Message, command: CommandObject):
    parts = (command.args or "").replace(","," ").split()
    if len(parts) < 2:
        await message.reply("<code>/sub a b</code>")
        return
    try:
        a, b = float(parts[0]), float(parts[1])
        if "sub" == "add": r = a + b
        elif "sub" == "sub": r = a - b
        elif "sub" == "mul": r = a * b
        else: r = a / b if b else 0
        await message.reply(card("Результат", f"<b>{r}</b>", emoji="🧮"))
    except Exception:
        await message.reply(fail("Числа"))

@router.message(Command("mul"))
async def cmd_mul(message: Message, command: CommandObject):
    parts = (command.args or "").replace(","," ").split()
    if len(parts) < 2:
        await message.reply("<code>/mul a b</code>")
        return
    try:
        a, b = float(parts[0]), float(parts[1])
        if "mul" == "add": r = a + b
        elif "mul" == "sub": r = a - b
        elif "mul" == "mul": r = a * b
        else: r = a / b if b else 0
        await message.reply(card("Результат", f"<b>{r}</b>", emoji="🧮"))
    except Exception:
        await message.reply(fail("Числа"))

@router.message(Command("div"))
async def cmd_div(message: Message, command: CommandObject):
    parts = (command.args or "").replace(","," ").split()
    if len(parts) < 2:
        await message.reply("<code>/div a b</code>")
        return
    try:
        a, b = float(parts[0]), float(parts[1])
        if "div" == "add": r = a + b
        elif "div" == "sub": r = a - b
        elif "div" == "mul": r = a * b
        else: r = a / b if b else 0
        await message.reply(card("Результат", f"<b>{r}</b>", emoji="🧮"))
    except Exception:
        await message.reply(fail("Числа"))
