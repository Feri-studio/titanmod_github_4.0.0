from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.commands import COMMANDS, CATEGORIES, ALL_COMMAND_NAMES
from core.style import HR, HR_LIGHT, CAT_EMOJI, card, safe_edit, unknown_command
from core.text import html_esc
from keyboards.inline import help_kb

router = Router()


async def start_kb(bot: Bot) -> InlineKeyboardMarkup:
    me = await bot.get_me()
    b = InlineKeyboardBuilder()
    if me.username:
        b.row(InlineKeyboardButton(
            text="➕ Добавить в группу",
            url=f"https://t.me/{me.username}?startgroup=true",
        ))
    b.row(
        InlineKeyboardButton(text="📚 Все команды", callback_data="cmds:all:0"),
        InlineKeyboardButton(text="❓ Справка", callback_data="help:home"),
    )
    b.row(InlineKeyboardButton(text="ℹ О боте", callback_data="help:about"))
    return b.as_markup()


def about_text() -> str:
    return (
        f"✨ <b>{config.BOT_NAME}</b>  <code>v{config.VERSION}</code>\n"
        f"{HR}\n"
        f"Telegram-бот модерации на aiogram 3.\n\n"
        f"› Наказания, варны, замки, капча\n"
        f"› Ранги, экономика, тикеты\n"
        f"› Автомод, федерации, розыгрыши\n"
        f"{HR_LIGHT}\n"
        f"<i>Сделай бота админом группы для полного функционала</i>"
    )


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message, command: CommandObject, bot: Bot):
    name = html_esc(message.from_user.first_name if message.from_user else "")
    text = (
        f"✨ <b>{config.BOT_NAME}</b>  <code>v{config.VERSION}</code>\n"
        f"{HR}\n"
        f"Привет, <b>{name}</b>! Я в этом чате.\n\n"
        f"<b>Админам</b>\n"
        f"› <code>/settings</code> — настройки\n"
        f"› <code>/commands</code> — каталог\n"
        f"› <code>/ranks</code> — штат\n"
        f"› <code>/rules</code> — правила\n"
        f"› <code>/preset normal</code> — автомод\n"
        f"{HR_LIGHT}\n"
        f"🏠 Кабинет в ЛС: <code>/menu</code>"
    )
    await message.reply(text, disable_web_page_preview=True)


@router.message(Command("help", "modhelp", "справка"))
async def cmd_help(message: Message):
    text = (
        f"❓ <b>Справка · {config.BOT_NAME}</b>\n"
        f"{HR}\n"
        f"В каталоге <b>{len(COMMANDS)}</b> команд.\n\n"
        f"› Выбери раздел на клавиатуре\n"
        f"› Полный список: <code>/commands</code>\n"
        f"› Неизвестная команда — бот пришлёт подсказку\n"
        f"{HR_LIGHT}\n"
        f"<i>TitanMod help</i>"
    )
    await message.reply(text, reply_markup=help_kb())


@router.callback_query(F.data.startswith("help:"))
async def help_cb(callback: CallbackQuery, bot: Bot):
    cat = callback.data.split(":", 1)[1]
    if cat == "about":
        await safe_edit(callback.message, about_text(), await start_kb(bot))
        await callback.answer()
        return
    if cat == "home":
        await safe_edit(
            callback.message,
            f"❓ <b>Справка · {config.BOT_NAME}</b>\n{HR}\n"
            f"Команд: <b>{len(COMMANDS)}</b>\nВыбери раздел:",
            help_kb(),
        )
        await callback.answer()
        return
    title = CATEGORIES.get(cat, cat)
    em = CAT_EMOJI.get(cat, "•")
    bits = [f"{em} <b>{html_esc(title)}</b>", HR]
    n = 0
    for cmd, c, desc in COMMANDS:
        if c != cat:
            continue
        bits.append(f"› <code>/{cmd}</code> — {html_esc(desc)}")
        n += 1
        if n >= 25:
            bits.append(f"<i>… и ещё в /commands</i>")
            break
    if n == 0:
        bits.append("<i>Пусто</i>")
    bits.append(HR_LIGHT)
    bits.append("<i>Назад — кнопка «Справка»</i>")
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="« К разделам", callback_data="help:home"))
    await safe_edit(callback.message, "\n".join(bits), b.as_markup())
    await callback.answer()


@router.message(Command("about", "version", "о"))
async def cmd_about(message: Message, bot: Bot):
    await message.reply(about_text(), reply_markup=await start_kb(bot), disable_web_page_preview=True)


@router.message(Command("privacy", "приваси"))
async def cmd_privacy(message: Message):
    await message.reply(
        card(
            "Приватность",
            "Бот хранит настройки чатов, варны, ранги и экономику в локальной SQLite.\n"
            "Сообщения пользователей не логируются целиком (кроме антиспам-кэша snipe в RAM).",
            footer="TitanMod",
            emoji="🔐",
        )
    )


@router.message(F.text.regexp(r"^/[A-Za-zа-яА-ЯёЁ0-9_]+"))
async def cmd_unknown(message: Message):
    """Fallback for unknown slash-commands."""
    text = (message.text or "").strip()
    if not text.startswith("/"):
        return
    raw = text[1:].split()[0].split("@")[0].lower()
    if raw in ALL_COMMAND_NAMES:
        return
    if len(raw) > 40:
        return
    await message.reply(unknown_command(raw), disable_web_page_preview=True)
