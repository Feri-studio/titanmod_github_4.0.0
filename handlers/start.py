from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.commands import COMMANDS, CATEGORIES, ALL_COMMAND_NAMES
from core.style import (
    HR, HR_LIGHT, CAT_EMOJI, card, safe_edit, unknown_command,
    welcome_private, welcome_group,
)
from core.text import html_esc
from keyboards.inline import help_kb

router = Router()


async def start_kb(bot: Bot) -> InlineKeyboardMarkup:
    me = await bot.get_me()
    b = InlineKeyboardBuilder()
    if me.username:
        b.row(InlineKeyboardButton(
            text="➕  Добавить в группу",
            url=f"https://t.me/{me.username}?startgroup=true",
        ))
    b.row(
        InlineKeyboardButton(text="📚  Все команды", callback_data="cmds:all:0"),
        InlineKeyboardButton(text="❓  Справка", callback_data="help:home"),
    )
    b.row(InlineKeyboardButton(text="ℹ️  О боте", callback_data="help:about"))
    return b.as_markup()


def about_text() -> str:
    return "\n".join([
        f"✨ <b>{config.BOT_NAME}</b>  <code>v{config.VERSION}</code>",
        HR,
        "Модерация групп в Telegram: чисто, быстро, по делу.",
        "",
        "<b>Умею</b>",
        "› Баны, муты, варны и замки контента",
        "› Капча, антирейд, фильтры и логи",
        "› Ранги штата, экономика, тикеты",
        "› Личный кабинет в ЛС",
        HR_LIGHT,
        "<i>Выдай боту права администратора — и можно настраивать чат</i>",
    ])


@router.message(Command("start"), F.chat.type == "private")
async def cmd_start_private(message: Message, bot: Bot):
    name = message.from_user.first_name if message.from_user else "друг"
    await message.reply(
        welcome_private(name, config.VERSION, config.BOT_NAME),
        reply_markup=await start_kb(bot),
        disable_web_page_preview=True,
    )


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message, command: CommandObject, bot: Bot):
    name = message.from_user.first_name if message.from_user else "друг"
    await message.reply(
        welcome_group(name, config.VERSION, config.BOT_NAME),
        disable_web_page_preview=True,
    )


@router.message(Command("help", "modhelp", "справка"))
async def cmd_help(message: Message):
    text = "\n".join([
        f"❓ <b>Справка · {config.BOT_NAME}</b>",
        HR,
        f"В каталоге <b>{len(COMMANDS)}</b> команд с описаниями.",
        "",
        "<b>Быстрые ссылки</b>",
        "› Разделы — кнопки ниже",
        "› Полный список: <code>/commands</code>",
        "› Кто я в чате: <code>/whoami</code>",
        "› Стата чата: <code>/chatstats</code>",
        HR_LIGHT,
        "<i>Не знаешь команду — напиши с ошибкой, подскажу</i>",
    ])
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
            "\n".join([
                f"❓ <b>Справка · {config.BOT_NAME}</b>",
                HR,
                f"Команд в каталоге: <b>{len(COMMANDS)}</b>",
                "Выбери раздел на клавиатуре.",
            ]),
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
            bits.append("<i>… полный список: /commands</i>")
            break
    if n == 0:
        bits.append("<i>В этом разделе пока пусто</i>")
    bits.extend([HR_LIGHT, "<i>Назад — кнопка «Справка»</i>"])
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="‹  К разделам", callback_data="help:home"))
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
            "\n".join([
                "Храню только необходимое для модерации:",
                "› настройки чата, варны, ранги, экономику",
                "› служебные логи действий",
                "",
                "Полные переписки не сохраняются.",
                "Snipe — только в памяти до перезапуска бота.",
            ]),
            footer="TitanMod · /privacy",
            emoji="🔐",
        )
    )


# @router.message(F.text.regexp(r"^/[A-Za-zа-яА-ЯёЁ0-9_]+"))
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


@router.message(Command("тест777"))
async def _test777(message: Message):
    await message.reply("РАБОТАЕТ! хендлер вызван")
