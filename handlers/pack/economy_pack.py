"""Economy extras with cooldowns — TitanMod 4.2."""
from __future__ import annotations

import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from core.style import ok, fail
from database.extra import add_coins, get_balance, check_cooldown, set_cooldown

router = Router()

WORK_CD = 300   # 5 min
CRIME_CD = 420  # 7 min
SLOTS_CD = 60


def _cd_msg(sec: int) -> str:
    m, s = divmod(sec, 60)
    return f"{m}м {s}с" if m else f"{s}с"


@router.message(Command("work"))
async def cmd_work(message: Message):
    if message.chat.type == "private":
        return
    ok_cd, left = await check_cooldown(message.chat.id, message.from_user.id, "work", WORK_CD)
    if not ok_cd:
        await message.reply(fail(f"Работа через {_cd_msg(left)}"))
        return
    pay = random.randint(15, 60)
    await set_cooldown(message.chat.id, message.from_user.id, "work")
    bal = await add_coins(message.chat.id, message.from_user.id, pay)
    await message.reply(ok(f"Смена закрыта: +<b>{pay}</b> · баланс <b>{bal}</b>"))


jobs = {
    "courier": (20, 40),
    "dev": (30, 70),
    "mod": (25, 55),
    "farmer": (15, 35),
    "miner": (20, 50),
    "trader": (25, 65),
    "guard": (20, 45),
    "chef": (15, 40),
    "driver": (20, 48),
    "artist": (22, 52),
}

for _job, (_lo, _hi) in jobs.items():
    def _make(job=_job, lo=_lo, hi=_hi):
        @router.message(Command(f"work_{job}", f"job_{job}"))
        async def _cmd(message: Message, job=job, lo=lo, hi=hi):
            if message.chat.type == "private":
                return
            ok_cd, left = await check_cooldown(message.chat.id, message.from_user.id, "work", WORK_CD)
            if not ok_cd:
                await message.reply(fail(f"Работа через {_cd_msg(left)}"))
                return
            pay = random.randint(lo, hi)
            await set_cooldown(message.chat.id, message.from_user.id, "work")
            bal = await add_coins(message.chat.id, message.from_user.id, pay)
            await message.reply(ok(f"Смена <b>{job}</b>: +<b>{pay}</b> · баланс <b>{bal}</b>"))
        return _cmd
    _make()


@router.message(Command("crime"))
async def cmd_crime(message: Message):
    if message.chat.type == "private":
        return
    ok_cd, left = await check_cooldown(message.chat.id, message.from_user.id, "crime", CRIME_CD)
    if not ok_cd:
        await message.reply(fail(f"Crime через {_cd_msg(left)}"))
        return
    await set_cooldown(message.chat.id, message.from_user.id, "crime")
    if random.random() < 0.45:
        loss = random.randint(10, 40)
        bal = await add_coins(message.chat.id, message.from_user.id, -loss)
        await message.reply(fail(f"Поймали! −<b>{loss}</b> · баланс <b>{bal}</b>"))
    else:
        gain = random.randint(20, 80)
        bal = await add_coins(message.chat.id, message.from_user.id, gain)
        await message.reply(ok(f"Удачно: +<b>{gain}</b> · баланс <b>{bal}</b>"))


@router.message(Command("slots"))
async def cmd_slots(message: Message):
    if message.chat.type == "private":
        return
    ok_cd, left = await check_cooldown(message.chat.id, message.from_user.id, "slots", SLOTS_CD)
    if not ok_cd:
        await message.reply(fail(f"Слоты через {_cd_msg(left)}"))
        return
    bal = await get_balance(message.chat.id, message.from_user.id)
    if bal < 10:
        await message.reply(fail("Нужно минимум 10 монет"))
        return
    await set_cooldown(message.chat.id, message.from_user.id, "slots")
    await add_coins(message.chat.id, message.from_user.id, -10)
    reels = [random.choice("🍒🍋🍇7️⃣⭐") for _ in range(3)]
    win = 50 if len(set(reels)) == 1 else (15 if len(set(reels)) == 2 else 0)
    if win:
        bal = await add_coins(message.chat.id, message.from_user.id, win)
        await message.reply(ok(f"{' '.join(reels)} · +<b>{win}</b> · баланс <b>{bal}</b>"))
    else:
        bal = await get_balance(message.chat.id, message.from_user.id)
        await message.reply(fail(f"{' '.join(reels)} · пусто · баланс <b>{bal}</b>"))
