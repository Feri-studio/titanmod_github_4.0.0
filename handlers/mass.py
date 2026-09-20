from aiogram import Router, Bot
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc, mention
from handlers.common import MUTE_PERMS, FREE_PERMS
from database.db import list_approved

router = Router()
router.message.filter(IsAdminFilter(), IsGroupFilter())


@router.message(Command("muteall"))
async def cmd_muteall(message: Message, bot: Bot):
    perms = ChatPermissions(can_send_messages=False)
    try:
        await bot.set_chat_permissions(message.chat.id, permissions=perms)
        await message.reply("Чат закрыт для всех (muteall). Админы пишут.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("unmuteallchat"))
async def cmd_unmuteallchat(message: Message, bot: Bot):
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    try:
        await bot.set_chat_permissions(message.chat.id, permissions=perms)
        await message.reply("Чат открыт.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("kickbots"))
async def cmd_kickbots(message: Message, bot: Bot):
    """Best-effort: kick other bots if admin list is available."""
    kicked = 0
    try:
        admins = await bot.get_chat_administrators(message.chat.id)
        admin_ids = {a.user.id for a in admins}
        me = await bot.get_me()
        # cannot enumerate all members without chat member list API; kick mentioned bots in reply chain
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
            uid = message.reply_to_message.from_user.id
            if uid != me.id and uid not in admin_ids:
                await bot.ban_chat_member(message.chat.id, uid)
                await bot.unban_chat_member(message.chat.id, uid)
                kicked += 1
    except Exception as e:
        await message.reply(html_esc(e))
        return
    await message.reply(f"Кикнуто ботов (из ответа): {kicked}")


@router.message(Command("approvedmute"))
async def cmd_amute(message: Message, bot: Bot):
    """Mute everyone except approved — implemented as closing chat; approved still need admin/rights."""
    n = len(await list_approved(message.chat.id))
    try:
        await bot.set_chat_permissions(message.chat.id, permissions=ChatPermissions(can_send_messages=False))
        await message.reply(f"Чат закрыт. Апрувнутых в списке: {n}. Им нужно быть админами или снять вручную.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("deluser"), )
async def cmd_deluser(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение — удалю это одно.")
        return
    try:
        await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        await message.delete()
    except Exception as e:
        await message.reply(html_esc(e))
