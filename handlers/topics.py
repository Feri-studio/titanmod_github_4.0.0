from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc

router = Router()
router.message.filter(IsGroupFilter(), IsAdminFilter())


@router.message(Command("newtopic", "тема"))
async def cmd_newtopic(message: Message, bot: Bot, command: CommandObject):
    name = (command.args or "").strip() or "Тема"
    try:
        topic = await bot.create_forum_topic(message.chat.id, name[:128])
        await message.reply(f"Тема создана: {html_esc(name)} (id {topic.message_thread_id})")
    except Exception as e:
        await message.reply(f"Не вышло: {html_esc(e)}")


@router.message(Command("closetopic"))
async def cmd_close(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        await message.reply("Пиши внутри темы.")
        return
    try:
        await bot.close_forum_topic(message.chat.id, tid)
        await message.reply("Тема закрыта.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("reopentopic"))
async def cmd_reopen(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        await message.reply("Пиши внутри темы.")
        return
    try:
        await bot.reopen_forum_topic(message.chat.id, tid)
        await message.reply("Тема открыта.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("renametopic"))
async def cmd_rename(message: Message, bot: Bot, command: CommandObject):
    tid = message.message_thread_id
    if not tid or not command.args:
        await message.reply("/renametopic новое имя  (внутри темы)")
        return
    try:
        await bot.edit_forum_topic(message.chat.id, tid, name=command.args[:128])
        await message.reply("Переименовано.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("hidetopic"))
async def cmd_hide(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        await message.reply("Пиши внутри темы.")
        return
    try:
        await bot.hide_general_forum_topic(message.chat.id)
        await message.reply("General скрыт (если это он).")
    except Exception:
        try:
            await bot.close_forum_topic(message.chat.id, tid)
            await message.reply("Тема закрыта.")
        except Exception as e:
            await message.reply(html_esc(e))


@router.message(Command("deletetopic"))
async def cmd_deltopic(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        await message.reply("Пиши внутри темы.")
        return
    try:
        await bot.delete_forum_topic(message.chat.id, tid)
    except Exception as e:
        await message.reply(html_esc(e))
