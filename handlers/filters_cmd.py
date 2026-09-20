from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc
from database.db import save_filter, get_filters, delete_filter, clear_filters
from utils.media import extract_media
from utils.buttons import parse_buttons

router = Router()
router.message.filter(IsGroupFilter())


@router.message(Command("filter"), IsAdminFilter())
async def cmd_filter(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/filter слово текст\nИли ответом: /filter слово")
        return
    parts = command.args.split(maxsplit=1)
    kw = parts[0]
    content = parts[1] if len(parts) > 1 else ""
    file_id = file_type = None
    if message.reply_to_message:
        file_id, file_type = extract_media(message.reply_to_message)
        if not content:
            content = message.reply_to_message.text or message.reply_to_message.caption or ""
    content, buttons = parse_buttons(content)
    await save_filter(message.chat.id, kw, content, message.from_user.id, file_id, file_type, buttons)
    await message.reply(f"Фильтр <code>{html_esc(kw)}</code> сохранён.")


@router.message(Command("stop"), IsAdminFilter())
async def cmd_stop(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/stop слово")
        return
    ok = await delete_filter(message.chat.id, command.args.strip())
    await message.reply("Удалён." if ok else "Нет такого фильтра.")


@router.message(Command("filters"), IsAdminFilter())
async def cmd_filters(message: Message):
    items = await get_filters(message.chat.id)
    if not items:
        await message.reply("Фильтров нет.")
        return
    await message.reply("Фильтры:\n" + ", ".join(f"<code>{html_esc(i['keyword'])}</code>" for i in items))


@router.message(Command("stopall"), IsAdminFilter())
async def cmd_stopall(message: Message):
    n = await clear_filters(message.chat.id)
    await message.reply(f"Удалено фильтров: {n}")
