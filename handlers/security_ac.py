""" /anticheat status for owners """
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import config
from core.anticheat import anticheat, MAX_PAY, MAX_COINFLIP, MAX_DAILY_BET_TOTAL
from core.style import HR, HR_LIGHT

router = Router()


@router.message(Command("anticheat", "античит", "acstatus"))
async def cmd_anticheat(message: Message):
    if not config.is_owner(message.from_user.id):
        await message.reply("🛡 Только владелец бота.")
        return
    score = anticheat.suspicion(message.from_user.id)
    text = "\n".join(
        [
            "🛡 <b>Античит TitanMod</b>",
            HR,
            f"› Лимит /pay: <code>{MAX_PAY}</code>",
            f"› Лимит /coinflip: <code>{MAX_COINFLIP}</code>",
            f"› Ставок в день: <code>{MAX_DAILY_BET_TOTAL}</code>",
            "› Антифлуд economy / punish / default",
            "› Команды от других ботов — блок",
            "› Длина ввода и подозрительные строки",
            "› Активация групп только по коду",
            HR_LIGHT,
            f"Suspicion score: <b>{score}</b>",
        ]
    )
    await message.reply(text)
