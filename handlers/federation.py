import uuid
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import mention, html_esc
from database.db import (
    create_fed, delete_fed, get_fed, get_fed_by_owner, join_fed, leave_fed,
    get_chat_fed, fed_ban, fed_unban, is_fbanned, fed_chats, fed_admins,
    fpromote, fdemote, list_fbans, update_settings, get_settings,
)
from handlers.common import resolve_user
from services.logger import send_log

router = Router()


@router.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject):
    name = (command.args or "").strip() or f"Fed {message.from_user.id}"
    existing = await get_fed_by_owner(message.from_user.id)
    if existing:
        await message.reply(f"У тебя уже есть федерация <code>{html_esc(existing['fed_id'])}</code> ({html_esc(existing['name'])}).")
        return
    fed_id = uuid.uuid4().hex[:10]
    await create_fed(fed_id, message.from_user.id, name)
    await message.reply(f"Федерация создана.\nИмя: {html_esc(name)}\nID: <code>{fed_id}</code>\nДобавь чат: /joinfed {fed_id}")


@router.message(Command("delfed"))
async def cmd_delfed(message: Message):
    fed = await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("У тебя нет федерации.")
        return
    await delete_fed(fed["fed_id"])
    await message.reply("Федерация удалена.")


@router.message(Command("renamefed"))
async def cmd_renamefed(message: Message, command: CommandObject):
    fed = await get_fed_by_owner(message.from_user.id)
    if not fed or not command.args:
        await message.reply("/renamefed новое имя")
        return
    from database.db import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE federations SET name=? WHERE fed_id=?", (command.args.strip(), fed["fed_id"]))
        await db.commit()
    await message.reply("Имя обновлено.")


@router.message(Command("joinfed"), IsAdminFilter(), IsGroupFilter())
async def cmd_joinfed(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/joinfed FED_ID")
        return
    fed = await get_fed(command.args.strip())
    if not fed:
        await message.reply("Федерация не найдена.")
        return
    if message.from_user.id != fed["owner_id"] and not await _is_fadmin(fed["fed_id"], message.from_user.id):
        # chat owner/admin can still join if they have the id — allow chat admins
        pass
    current = await get_chat_fed(message.chat.id)
    if current:
        await message.reply("Чат уже в федерации. Сначала /leavefed")
        return
    await join_fed(fed["fed_id"], message.chat.id)
    await update_settings(message.chat.id, federation_id=fed["fed_id"])
    await message.reply(f"Чат вступил в федерацию {html_esc(fed['name'])}")


@router.message(Command("leavefed"), IsAdminFilter(), IsGroupFilter())
async def cmd_leavefed(message: Message):
    fed = await get_chat_fed(message.chat.id)
    if not fed:
        await message.reply("Чат не в федерации.")
        return
    await leave_fed(fed["fed_id"], message.chat.id)
    await update_settings(message.chat.id, federation_id="")
    await message.reply("Чат вышел из федерации.")


@router.message(Command("fedinfo"))
async def cmd_fedinfo(message: Message, command: CommandObject):
    fed_id = (command.args or "").strip()
    fed = await get_fed(fed_id) if fed_id else await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("Федерация не найдена.")
        return
    chats = await fed_chats(fed["fed_id"])
    bans = await list_fbans(fed["fed_id"])
    await message.reply(
        f"<b>{html_esc(fed['name'])}</b>\n"
        f"ID: <code>{fed['fed_id']}</code>\n"
        f"Владелец: <code>{fed['owner_id']}</code>\n"
        f"Чатов: {len(chats)}\n"
        f"Банов: {len(bans)}"
    )


@router.message(Command("fedchats"))
async def cmd_fedchats(message: Message):
    fed = await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("Нет федерации.")
        return
    chats = await fed_chats(fed["fed_id"])
    await message.reply("Чаты:\n" + "\n".join(f"<code>{c}</code>" for c in chats) or "пусто")


@router.message(Command("fban"), IsAdminFilter())
async def cmd_fban(message: Message, bot: Bot, command: CommandObject):
    fed = await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("Нет федерации.")
        return
    if not await _is_fadmin(fed["fed_id"], message.from_user.id) and message.from_user.id != fed["owner_id"]:
        await message.reply("Ты не фед-админ.")
        return
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    reason = rest or "Федбан"
    await fed_ban(fed["fed_id"], user.id, message.from_user.id, reason)
    chats = await fed_chats(fed["fed_id"])
    ok = 0
    for cid in chats:
        try:
            await bot.ban_chat_member(cid, user.id)
            ok += 1
        except Exception:
            pass
    await send_log(bot, message.chat.id, "fban", f"FBAN {mention(user)} reason={html_esc(reason)} chats={ok}", user.id, message.from_user.id)
    await message.reply(f"Федбан {mention(user)}\nПричина: {html_esc(reason)}\nЧатов: {ok}/{len(chats)}")


@router.message(Command("unfban"), IsAdminFilter())
async def cmd_unfban(message: Message, bot: Bot, command: CommandObject):
    fed = await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        return
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    await fed_unban(fed["fed_id"], user.id)
    for cid in await fed_chats(fed["fed_id"]):
        try:
            await bot.unban_chat_member(cid, user.id, only_if_banned=True)
        except Exception:
            pass
    await message.reply(f"Снят федбан с {mention(user)}")


@router.message(Command("fbans"))
async def cmd_fbans(message: Message):
    fed = await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        return
    bans = await list_fbans(fed["fed_id"])
    if not bans:
        await message.reply("Федбанов нет.")
        return
    lines = [f"{i}. <code>{b['user_id']}</code> — {html_esc(b['reason'])}" for i, b in enumerate(bans[:50], 1)]
    await message.reply("Федбаны:\n" + "\n".join(lines))


@router.message(Command("fpromote"))
async def cmd_fpromote(message: Message, bot: Bot, command: CommandObject):
    fed = await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("Только владелец федерации.")
        return
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    await fpromote(fed["fed_id"], user.id)
    await message.reply(f"{mention(user)} теперь фед-админ.")


@router.message(Command("fdemote"))
async def cmd_fdemote(message: Message, bot: Bot, command: CommandObject):
    fed = await get_fed_by_owner(message.from_user.id)
    if not fed:
        return
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    await fdemote(fed["fed_id"], user.id)
    await message.reply("Снят.")


@router.message(Command("fedadmins"))
async def cmd_fedadmins(message: Message):
    fed = await get_chat_fed(message.chat.id) or await get_fed_by_owner(message.from_user.id)
    if not fed:
        return
    admins = await fed_admins(fed["fed_id"])
    await message.reply("Фед-админы:\n" + "\n".join(f"<code>{a}</code>" for a in admins))


@router.message(Command("myfeds"))
async def cmd_myfeds(message: Message):
    fed = await get_fed_by_owner(message.from_user.id)
    if not fed:
        await message.reply("Нет своей федерации. /newfed имя")
        return
    await message.reply(f"{html_esc(fed['name'])} — <code>{fed['fed_id']}</code>")


async def _is_fadmin(fed_id, user_id) -> bool:
    admins = await fed_admins(fed_id)
    return user_id in admins
