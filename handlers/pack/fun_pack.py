"""Expanded fun commands pack."""
from __future__ import annotations
import random
import hashlib
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from core.style import card
from core.text import html_esc

router = Router()
JOKES = ['Почему программисты путают Хэллоуин и Рождество? Потому что OCT 31 == DEC 25.', 'Баг — это не ошибка, это неодокументированная фича.', 'У админа нет проблем — только инциденты.', 'Сначала работает, потом красиво, потом быстро. Выбери два.', 'Заработал на багах — купил себе feature.']

@router.message(Command("joke1"))
async def cmd_joke_1(message: Message):
    await message.reply(card("Шутка #1", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke2"))
async def cmd_joke_2(message: Message):
    await message.reply(card("Шутка #2", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke3"))
async def cmd_joke_3(message: Message):
    await message.reply(card("Шутка #3", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke4"))
async def cmd_joke_4(message: Message):
    await message.reply(card("Шутка #4", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke5"))
async def cmd_joke_5(message: Message):
    await message.reply(card("Шутка #5", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke6"))
async def cmd_joke_6(message: Message):
    await message.reply(card("Шутка #6", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke7"))
async def cmd_joke_7(message: Message):
    await message.reply(card("Шутка #7", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke8"))
async def cmd_joke_8(message: Message):
    await message.reply(card("Шутка #8", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke9"))
async def cmd_joke_9(message: Message):
    await message.reply(card("Шутка #9", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke10"))
async def cmd_joke_10(message: Message):
    await message.reply(card("Шутка #10", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke11"))
async def cmd_joke_11(message: Message):
    await message.reply(card("Шутка #11", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke12"))
async def cmd_joke_12(message: Message):
    await message.reply(card("Шутка #12", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke13"))
async def cmd_joke_13(message: Message):
    await message.reply(card("Шутка #13", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke14"))
async def cmd_joke_14(message: Message):
    await message.reply(card("Шутка #14", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke15"))
async def cmd_joke_15(message: Message):
    await message.reply(card("Шутка #15", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke16"))
async def cmd_joke_16(message: Message):
    await message.reply(card("Шутка #16", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke17"))
async def cmd_joke_17(message: Message):
    await message.reply(card("Шутка #17", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke18"))
async def cmd_joke_18(message: Message):
    await message.reply(card("Шутка #18", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke19"))
async def cmd_joke_19(message: Message):
    await message.reply(card("Шутка #19", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke20"))
async def cmd_joke_20(message: Message):
    await message.reply(card("Шутка #20", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke21"))
async def cmd_joke_21(message: Message):
    await message.reply(card("Шутка #21", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke22"))
async def cmd_joke_22(message: Message):
    await message.reply(card("Шутка #22", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke23"))
async def cmd_joke_23(message: Message):
    await message.reply(card("Шутка #23", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke24"))
async def cmd_joke_24(message: Message):
    await message.reply(card("Шутка #24", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke25"))
async def cmd_joke_25(message: Message):
    await message.reply(card("Шутка #25", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke26"))
async def cmd_joke_26(message: Message):
    await message.reply(card("Шутка #26", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke27"))
async def cmd_joke_27(message: Message):
    await message.reply(card("Шутка #27", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke28"))
async def cmd_joke_28(message: Message):
    await message.reply(card("Шутка #28", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke29"))
async def cmd_joke_29(message: Message):
    await message.reply(card("Шутка #29", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke30"))
async def cmd_joke_30(message: Message):
    await message.reply(card("Шутка #30", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke31"))
async def cmd_joke_31(message: Message):
    await message.reply(card("Шутка #31", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke32"))
async def cmd_joke_32(message: Message):
    await message.reply(card("Шутка #32", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke33"))
async def cmd_joke_33(message: Message):
    await message.reply(card("Шутка #33", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke34"))
async def cmd_joke_34(message: Message):
    await message.reply(card("Шутка #34", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke35"))
async def cmd_joke_35(message: Message):
    await message.reply(card("Шутка #35", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("joke36"))
async def cmd_joke_36(message: Message):
    await message.reply(card("Шутка #36", html_esc(JOKES[1]), emoji="😂"))

@router.message(Command("joke37"))
async def cmd_joke_37(message: Message):
    await message.reply(card("Шутка #37", html_esc(JOKES[2]), emoji="😂"))

@router.message(Command("joke38"))
async def cmd_joke_38(message: Message):
    await message.reply(card("Шутка #38", html_esc(JOKES[3]), emoji="😂"))

@router.message(Command("joke39"))
async def cmd_joke_39(message: Message):
    await message.reply(card("Шутка #39", html_esc(JOKES[4]), emoji="😂"))

@router.message(Command("joke40"))
async def cmd_joke_40(message: Message):
    await message.reply(card("Шутка #40", html_esc(JOKES[0]), emoji="😂"))

@router.message(Command("rate1"))
async def cmd_rate_1(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:1"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate2"))
async def cmd_rate_2(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:2"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate3"))
async def cmd_rate_3(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:3"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate4"))
async def cmd_rate_4(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:4"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate5"))
async def cmd_rate_5(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:5"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate6"))
async def cmd_rate_6(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:6"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate7"))
async def cmd_rate_7(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:7"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate8"))
async def cmd_rate_8(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:8"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate9"))
async def cmd_rate_9(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:9"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate10"))
async def cmd_rate_10(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:10"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate11"))
async def cmd_rate_11(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:11"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate12"))
async def cmd_rate_12(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:12"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate13"))
async def cmd_rate_13(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:13"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate14"))
async def cmd_rate_14(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:14"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate15"))
async def cmd_rate_15(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:15"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate16"))
async def cmd_rate_16(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:16"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate17"))
async def cmd_rate_17(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:17"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate18"))
async def cmd_rate_18(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:18"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate19"))
async def cmd_rate_19(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:19"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate20"))
async def cmd_rate_20(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:20"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate21"))
async def cmd_rate_21(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:21"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate22"))
async def cmd_rate_22(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:22"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate23"))
async def cmd_rate_23(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:23"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate24"))
async def cmd_rate_24(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:24"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate25"))
async def cmd_rate_25(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:25"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate26"))
async def cmd_rate_26(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:26"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate27"))
async def cmd_rate_27(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:27"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate28"))
async def cmd_rate_28(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:28"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate29"))
async def cmd_rate_29(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:29"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate30"))
async def cmd_rate_30(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:30"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate31"))
async def cmd_rate_31(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:31"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate32"))
async def cmd_rate_32(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:32"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate33"))
async def cmd_rate_33(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:33"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate34"))
async def cmd_rate_34(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:34"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate35"))
async def cmd_rate_35(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:35"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate36"))
async def cmd_rate_36(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:36"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate37"))
async def cmd_rate_37(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:37"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate38"))
async def cmd_rate_38(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:38"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate39"))
async def cmd_rate_39(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:39"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("rate40"))
async def cmd_rate_40(message: Message, command: CommandObject):
    target = (command.args or "").strip()
    if not target and message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.first_name or "user"
    if not target:
        target = "это"
    seed = f"{message.from_user.id}:{target}:40"
    val = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Оценка", f"{html_esc(str(target)[:80])}: <b>{val}/100</b>", emoji="📊"))

@router.message(Command("roll1"))
async def cmd_roll_1(message: Message):
    await message.reply(card("Roll", f"d10: <b>{random.randint(1, 10)}</b>", emoji="🎲"))

@router.message(Command("roll2"))
async def cmd_roll_2(message: Message):
    await message.reply(card("Roll", f"d20: <b>{random.randint(1, 20)}</b>", emoji="🎲"))

@router.message(Command("roll3"))
async def cmd_roll_3(message: Message):
    await message.reply(card("Roll", f"d30: <b>{random.randint(1, 30)}</b>", emoji="🎲"))

@router.message(Command("roll4"))
async def cmd_roll_4(message: Message):
    await message.reply(card("Roll", f"d40: <b>{random.randint(1, 40)}</b>", emoji="🎲"))

@router.message(Command("roll5"))
async def cmd_roll_5(message: Message):
    await message.reply(card("Roll", f"d50: <b>{random.randint(1, 50)}</b>", emoji="🎲"))

@router.message(Command("roll6"))
async def cmd_roll_6(message: Message):
    await message.reply(card("Roll", f"d60: <b>{random.randint(1, 60)}</b>", emoji="🎲"))

@router.message(Command("roll7"))
async def cmd_roll_7(message: Message):
    await message.reply(card("Roll", f"d70: <b>{random.randint(1, 70)}</b>", emoji="🎲"))

@router.message(Command("roll8"))
async def cmd_roll_8(message: Message):
    await message.reply(card("Roll", f"d80: <b>{random.randint(1, 80)}</b>", emoji="🎲"))

@router.message(Command("roll9"))
async def cmd_roll_9(message: Message):
    await message.reply(card("Roll", f"d90: <b>{random.randint(1, 90)}</b>", emoji="🎲"))

@router.message(Command("roll10"))
async def cmd_roll_10(message: Message):
    await message.reply(card("Roll", f"d100: <b>{random.randint(1, 100)}</b>", emoji="🎲"))

@router.message(Command("roll11"))
async def cmd_roll_11(message: Message):
    await message.reply(card("Roll", f"d110: <b>{random.randint(1, 110)}</b>", emoji="🎲"))

@router.message(Command("roll12"))
async def cmd_roll_12(message: Message):
    await message.reply(card("Roll", f"d120: <b>{random.randint(1, 120)}</b>", emoji="🎲"))

@router.message(Command("roll13"))
async def cmd_roll_13(message: Message):
    await message.reply(card("Roll", f"d130: <b>{random.randint(1, 130)}</b>", emoji="🎲"))

@router.message(Command("roll14"))
async def cmd_roll_14(message: Message):
    await message.reply(card("Roll", f"d140: <b>{random.randint(1, 140)}</b>", emoji="🎲"))

@router.message(Command("roll15"))
async def cmd_roll_15(message: Message):
    await message.reply(card("Roll", f"d150: <b>{random.randint(1, 150)}</b>", emoji="🎲"))

@router.message(Command("roll16"))
async def cmd_roll_16(message: Message):
    await message.reply(card("Roll", f"d160: <b>{random.randint(1, 160)}</b>", emoji="🎲"))

@router.message(Command("roll17"))
async def cmd_roll_17(message: Message):
    await message.reply(card("Roll", f"d170: <b>{random.randint(1, 170)}</b>", emoji="🎲"))

@router.message(Command("roll18"))
async def cmd_roll_18(message: Message):
    await message.reply(card("Roll", f"d180: <b>{random.randint(1, 180)}</b>", emoji="🎲"))

@router.message(Command("roll19"))
async def cmd_roll_19(message: Message):
    await message.reply(card("Roll", f"d190: <b>{random.randint(1, 190)}</b>", emoji="🎲"))

@router.message(Command("roll20"))
async def cmd_roll_20(message: Message):
    await message.reply(card("Roll", f"d200: <b>{random.randint(1, 200)}</b>", emoji="🎲"))
