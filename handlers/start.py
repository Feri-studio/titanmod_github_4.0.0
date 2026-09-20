from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.commands import COMMANDS, CATEGORIES, HELP_TEXT, ALL_COMMAND_NAMES
from core.style import HR, CAT_EMOJI, card, safe_edit
from core.text import html_esc
from database.db import get_connection
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


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    extra = ""
    conn = await get_connection(message.from_user.id)
    if conn:
        extra = f"\n🔗 Привязан чат: <code>{conn}</code>"
    args = command.args or ""
    if args == "help":
        await cmd_help(message)
        return
    name = html_esc(message.from_user.first_name if message.from_user else "")
    text = (
        f"✦ <b>{config.BOT_NAME}</b>  <code>v{config.VERSION}</code>\n"
        f"Привет, {name}!\n"
        f"{HR}\n"
        f"Я держу чат в порядке — красиво и жёстко, когда надо.\n\n"
        f"🔨 баны · муты · варны · карантин\n"
        f"🔒 40+ замков контента · антифлуд · антирейд\n"
        f"👋 капча · приветствия · правила\n"
        f"📝 заметки · фильтры · розыгрыши · XP\n"
        f"{HR}\n"
        f"<b>Как включить</b>\n"
        f"1. Добавь меня в группу\n"
        f"2. Дай права: удаление сообщений + блокировка\n"
        f"3. Напиши <code>/settings</code> и <code>/commands</code>\n"
        f"{extra}\n\n"
        f"<i>{len(ALL_COMMAND_NAMES)} команд · жми кнопки ниже</i>"
    )
    await message.reply(text, reply_markup=await start_kb(bot), disable_web_page_preview=True)


@router.message(Command("help", "modhelp", "справка"))
async def cmd_help(message: Message):
    text = (
        f"❓ <b>Справка {config.BOT_NAME}</b>\n"
        f"{HR}\n"
        f"Команд в боте: <b>{len(COMMANDS)}</b>\n"
        f"Выбери раздел — или открой полный каталог <code>/commands</code>"
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
            f"❓ <b>Справка {config.BOT_NAME}</b>\n{HR}\nКоманд: <b>{len(COMMANDS)}</b>\nВыбери раздел:",
            help_kb(),
        )
        await callback.answer()
        return
    title = CATEGORIES.get(cat, cat)
    em = CAT_EMOJI.get(cat, "•")
    bits = [f"{em} <b>{html_esc(title)}</b>", HR]
    for cmd, c, desc in COMMANDS:
        if c != cat:
            continue
        bits.append(f"• <code>/{html_esc(cmd)}</code> — {html_esc(desc)}")
    bits.append(HR)
    bits.append(f"<code>/commands {html_esc(cat)}</code>")
    text = "\n".join(bits)
    if len(text) > 3900:
        text = text[:3890] + "…"
    await safe_edit(callback.message, text, help_kb())
    await callback.answer()


def about_text() -> str:
    return (
        f"✦ <b>{config.BOT_NAME}</b> <code>{config.VERSION}</code>\n"
        f"{HR}\n"
        f"Стек: Python · aiogram 3 · SQLite\n"
        f"Разделов: {len(CATEGORIES)} · команд: {len(ALL_COMMAND_NAMES)}\n"
        f"Данные живут у тебя в файле базы, никуда не улетают.\n"
        f"{HR}\n"
        f"<code>/commands</code> · <code>/privacy</code> · <code>/settings</code>"
    )


@router.message(Command("about", "version", "о"))
async def cmd_about(message: Message, bot: Bot):
    await message.reply(about_text(), reply_markup=await start_kb(bot))


@router.message(Command("privacy", "приваси"))
async def cmd_privacy(message: Message):
    await message.reply(
        card(
            "🔒 Приватность",
            "Храню: id чатов и людей, настройки, варны, заметки, логи наказаний.\n"
            "Не продаю и не скармливаю рекламе.\n"
            "Админ чата может сбросить конфиг: <code>/resetchat</code>",
        )
    )
