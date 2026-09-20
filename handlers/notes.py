from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc, mention
from database.db import (
    save_note, get_note, list_notes, delete_note, clear_notes, get_settings,
    set_custom_command, get_custom_command, list_custom_commands, delete_custom_command,
)
from utils.media import extract_media, send_saved
from utils.buttons import parse_buttons, build_markup

router = Router()


@router.message(Command("save"), IsAdminFilter(), IsGroupFilter())
async def cmd_save(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/save имя текст\nИли ответом на сообщение: /save имя")
        return
    parts = command.args.split(maxsplit=1)
    name = parts[0].lower()
    content = parts[1] if len(parts) > 1 else ""
    file_id = file_type = None
    if message.reply_to_message:
        file_id, file_type = extract_media(message.reply_to_message)
        if not content:
            content = message.reply_to_message.text or message.reply_to_message.caption or ""
    content, buttons = parse_buttons(content)
    await save_note(message.chat.id, name, content, message.from_user.id, file_id, file_type, buttons)
    await message.reply(f"Заметка <code>{html_esc(name)}</code> сохранена.")


@router.message(Command("get"))
async def cmd_get(message: Message, bot: Bot, command: CommandObject):
    if not command.args:
        await message.reply("/get имя")
        return
    await _send_note(message, bot, command.args.strip().split()[0])


@router.message(Command("notes"), IsGroupFilter())
async def cmd_notes(message: Message):
    names = await list_notes(message.chat.id)
    if not names:
        await message.reply("Заметок нет. /save имя текст")
        return
    await message.reply("Заметки:\n" + ", ".join(f"<code>#{n}</code>" for n in names))


@router.message(Command("clear"), IsAdminFilter(), IsGroupFilter())
async def cmd_clear_note(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/clear имя")
        return
    ok = await delete_note(message.chat.id, command.args.strip())
    await message.reply("Удалено." if ok else "Нет такой заметки.")


@router.message(Command("clearallnotes"), IsAdminFilter(), IsGroupFilter())
async def cmd_clear_all(message: Message):
    n = await clear_notes(message.chat.id)
    await message.reply(f"Удалено заметок: {n}")


@router.message(Command("privatenotes"), IsAdminFilter(), IsGroupFilter())
async def cmd_privnotes(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    from database.db import update_settings
    await update_settings(message.chat.id, privatenotes=1 if on else 0)
    await message.reply("privatenotes " + ("on" if on else "off"))


@router.message(Command("addcmd"), IsAdminFilter(), IsGroupFilter())
async def cmd_addcmd(message: Message, command: CommandObject):
    if not command.args or len(command.args.split(maxsplit=1)) < 2:
        await message.reply("/addcmd команда текст")
        return
    name, content = command.args.split(maxsplit=1)
    await set_custom_command(message.chat.id, name.lstrip("/"), content)
    await message.reply(f"Команда /{html_esc(name.lstrip('/'))} сохранена.")


@router.message(Command("delcmd"), IsAdminFilter(), IsGroupFilter())
async def cmd_delcmd(message: Message, command: CommandObject):
    if not command.args:
        return
    ok = await delete_custom_command(message.chat.id, command.args.strip().lstrip("/"))
    await message.reply("Удалено." if ok else "Нет такой команды.")


@router.message(Command("cmds"), IsGroupFilter())
async def cmd_cmds(message: Message):
    items = await list_custom_commands(message.chat.id)
    if not items:
        await message.reply("Кастомных команд нет.")
        return
    await message.reply("Команды:\n" + "\n".join(f"/{a}" for a, _ in items))


@router.message(F.text.regexp(r"^#\w+"))
async def hash_note(message: Message, bot: Bot):
    if message.chat.type not in ("group", "supergroup"):
        return
    name = message.text[1:].split()[0].lower()
    await _send_note(message, bot, name, silent=True)


async def _send_note(message: Message, bot: Bot, name: str, silent=False):
    note = await get_note(message.chat.id, name)
    if not note:
        if not silent:
            await message.reply("Нет такой заметки.")
        return
    s = await get_settings(message.chat.id)
    markup = build_markup(note.get("buttons"))
    dest = message.from_user.id if s.get("privatenotes") else message.chat.id
    try:
        await send_saved(bot, dest, note.get("content") or "", note.get("file_id"), note.get("file_type"), markup, None if s.get("privatenotes") else message.message_id)
        if s.get("privatenotes") and message.chat.type != "private":
            await message.reply("Отправил в ЛС.")
    except Exception as e:
        if dest != message.chat.id:
            await send_saved(bot, message.chat.id, note.get("content") or "", note.get("file_id"), note.get("file_type"), markup, message.message_id)
        else:
            await message.reply(f"Не удалось отправить: {html_esc(e)}")
