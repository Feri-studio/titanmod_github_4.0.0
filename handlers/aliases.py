from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc
from database.extra import add_alias, del_alias, list_aliases
from core.commands import ALL_COMMAND_NAMES
from core.style import HR

router = Router()


@router.message(Command("addalias"), IsAdminFilter(), IsGroupFilter())
async def cmd_addalias(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("✨ <code>/addalias кик kick</code>\nДальше <code>/кик</code> сработает как <code>/kick</code>.")
        return
    parts = command.args.split()
    if len(parts) < 2:
        await message.reply("Нужны алиас и команда.")
        return
    alias, cmd = parts[0], parts[1]
    if cmd.lstrip("/") not in ALL_COMMAND_NAMES:
        await message.reply("Не знаю такую команду-цель. Смотри <code>/commands</code>.")
        return
    await add_alias(message.chat.id, alias, cmd)
    await message.reply(f"✨ <code>/{html_esc(alias)}</code> → <code>/{html_esc(cmd)}</code>")


@router.message(Command("delalias"), IsAdminFilter(), IsGroupFilter())
async def cmd_delalias(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("<code>/delalias кик</code>")
        return
    ok = await del_alias(message.chat.id, command.args.strip())
    await message.reply("Удалено." if ok else "Нет такого алиаса.")


@router.message(Command("aliases"), IsAdminFilter(), IsGroupFilter())
async def cmd_aliases(message: Message):
    items = await list_aliases(message.chat.id)
    if not items:
        await message.reply("Алиасов нет. Добавь: <code>/addalias кик kick</code>")
        return
    lines = ["✨ <b>Алиасы</b>", HR]
    lines += [f"<code>/{a}</code> → <code>/{c}</code>" for a, c in items]
    await message.reply("\n".join(lines))
