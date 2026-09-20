import json
from aiogram import Router, Bot, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter, IsOwnerFilter
from core.text import html_esc
from database.db import export_chat, get_settings, update_settings, ensure_chat

router = Router()


@router.message(Command("backup", "экспорт"), IsAdminFilter(), IsGroupFilter())
async def cmd_backup(message: Message):
    data = await export_chat(message.chat.id)
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    await message.answer_document(
        BufferedInputFile(raw, filename=f"backup_{message.chat.id}.json"),
        caption="Бэкап настроек, заметок и фильтров.",
    )


@router.message(Command("importbackup"), IsAdminFilter(), IsGroupFilter())
async def cmd_import(message: Message):
    src = message.reply_to_message
    if not src or not src.document:
        await message.reply("Ответь на JSON-файл бэкапа.")
        return
    try:
        file = await message.bot.download(src.document)
        payload = json.loads(file.read().decode("utf-8"))
    except Exception as e:
        await message.reply(f"Не прочитался JSON: {html_esc(e)}")
        return
    settings = payload.get("settings") or {}
    if isinstance(settings, dict) and settings:
        await update_settings(message.chat.id, **{k: v for k, v in settings.items() if k})
    await message.reply("Настройки из бэкапа применены (фильтры/заметки импортируй вручную при необходимости).")


@router.message(Command("dumpsettings"), IsAdminFilter(), IsGroupFilter())
async def cmd_dump(message: Message):
    s = await get_settings(message.chat.id)
    text = json.dumps(s, ensure_ascii=False, indent=2)
    if len(text) > 3500:
        await message.answer_document(BufferedInputFile(text.encode(), filename="settings.json"))
        return
    await message.reply(f"<pre>{html_esc(text)}</pre>")
