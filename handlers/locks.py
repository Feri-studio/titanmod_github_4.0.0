from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.defaults import LOCK_TYPES, BLACKLIST_MODES, FLOOD_MODES
from core.text import html_esc
from database.db import (
    get_settings, update_settings, add_badword, remove_badword, get_badwords,
    add_whitelist, remove_whitelist, get_whitelist, add_bl_sticker,
)
from services.locks import parse_lock_set, dump_lock_set

router = Router()
router.message.filter(IsGroupFilter())


@router.message(Command("locktypes"), IsAdminFilter())
async def cmd_locktypes(message: Message):
    lines = ["Доступные замки:"]
    for k, v in LOCK_TYPES.items():
        lines.append(f"• <code>{k}</code> — {v}")
    text = "\n".join(lines)
    if len(text) > 4000:
        await message.reply("\n".join(lines[:40]))
        await message.answer("\n".join(lines[40:]))
    else:
        await message.reply(text)


@router.message(Command("locks"), IsAdminFilter())
async def cmd_locks(message: Message):
    s = await get_settings(message.chat.id)
    enabled = parse_lock_set(s.get("locks"))
    if not enabled:
        await message.reply("Все замки выключены. /locktypes")
        return
    await message.reply("Включены:\n" + "\n".join(f"• {k} — {LOCK_TYPES.get(k, k)}" for k in sorted(enabled)))


@router.message(Command("lock"), IsAdminFilter())
async def cmd_lock(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if not arg or arg not in LOCK_TYPES:
        await message.reply("Укажи тип: /lock url\nСписок: /locktypes")
        return
    s = await get_settings(message.chat.id)
    enabled = parse_lock_set(s.get("locks"))
    enabled.add(arg)
    await update_settings(message.chat.id, locks=dump_lock_set(enabled))
    await message.reply(f"Замок <code>{arg}</code> включён.")


@router.message(Command("unlock"), IsAdminFilter())
async def cmd_unlock(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    s = await get_settings(message.chat.id)
    enabled = parse_lock_set(s.get("locks"))
    if arg == "all":
        await update_settings(message.chat.id, locks="")
        await message.reply("Все замки сняты.")
        return
    if arg not in enabled:
        await message.reply("Этот замок не включён.")
        return
    enabled.discard(arg)
    await update_settings(message.chat.id, locks=dump_lock_set(enabled))
    await message.reply(f"Замок <code>{arg}</code> выключен.")


@router.message(Command("lockwarns"), IsAdminFilter())
async def cmd_lockwarns(message: Message, command: CommandObject):
    arg = (command.args or "on").strip().lower()
    on = arg in ("on", "1", "true", "yes", "да")
    await update_settings(message.chat.id, lock_warn=1 if on else 0)
    await message.reply("Предупреждения замков " + ("включены" if on else "выключены"))


@router.message(Command("addbadword", "blacklist"), IsAdminFilter())
async def cmd_addbad(message: Message, command: CommandObject):
    if command.command == "blacklist" and not command.args:
        words = await get_badwords(message.chat.id)
        await message.reply("Чёрный список:\n" + (", ".join(f"<code>{html_esc(w)}</code>" for w in words) or "пусто"))
        return
    if not command.args:
        await message.reply("/addbadword слово")
        return
    ok = await add_badword(message.chat.id, command.args.strip())
    await message.reply("Добавлено." if ok else "Уже есть.")


@router.message(Command("delbadword"), IsAdminFilter())
async def cmd_delbad(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/delbadword слово")
        return
    await remove_badword(message.chat.id, command.args.strip())
    await message.reply("Удалено.")


@router.message(Command("badwords"), IsAdminFilter())
async def cmd_badwords(message: Message):
    words = await get_badwords(message.chat.id)
    await message.reply("Чёрный список:\n" + (", ".join(f"<code>{html_esc(w)}</code>" for w in words) or "пусто"))


@router.message(Command("blacklistmode"), IsAdminFilter())
async def cmd_blmode(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if arg not in BLACKLIST_MODES:
        await message.reply("Режимы: " + ", ".join(BLACKLIST_MODES))
        return
    await update_settings(message.chat.id, blacklist_mode=arg)
    await message.reply(f"Режим чёрного списка: {arg}")


@router.message(Command("addwhite"), IsAdminFilter())
async def cmd_addwhite(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/addwhite example.com")
        return
    domain = command.args.lower().strip().replace("https://", "").replace("http://", "").split("/")[0]
    ok = await add_whitelist(message.chat.id, domain)
    await message.reply("Добавлено." if ok else "Уже есть.")


@router.message(Command("delwhite"), IsAdminFilter())
async def cmd_delwhite(message: Message, command: CommandObject):
    if not command.args:
        return
    await remove_whitelist(message.chat.id, command.args.strip())
    await message.reply("Удалено.")


@router.message(Command("whitelist"), IsAdminFilter())
async def cmd_white(message: Message):
    d = await get_whitelist(message.chat.id)
    await message.reply("Белые домены:\n" + (", ".join(f"<code>{x}</code>" for x in d) or "пусто"))


@router.message(Command("blsticker"), IsAdminFilter())
async def cmd_blsticker(message: Message):
    src = message.reply_to_message
    if not src or not src.sticker:
        await message.reply("Ответь на стикер.")
        return
    await add_bl_sticker(message.chat.id, src.sticker.file_unique_id, src.sticker.set_name or "")
    await message.reply("Стикер добавлен в чёрный список.")


@router.message(Command("setflood"), IsAdminFilter())
async def cmd_setflood(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setflood 6 8 — 6 сообщений за 8 секунд")
        return
    try:
        a = command.args.split()
        limit, period = int(a[0]), int(a[1]) if len(a) > 1 else 8
        await update_settings(message.chat.id, flood_limit=limit, flood_period=period, antiflood=1)
        await message.reply(f"Антифлуд: {limit} сообщ. / {period} сек.")
    except Exception:
        await message.reply("Неверный формат.")


@router.message(Command("flood"), IsAdminFilter())
async def cmd_flood(message: Message):
    s = await get_settings(message.chat.id)
    await message.reply(
        f"Антифлуд: {'вкл' if s.get('antiflood') else 'выкл'}\n"
        f"Лимит: {s.get('flood_limit')} / {s.get('flood_period')}с\n"
        f"Режим: {s.get('flood_mode')} ({s.get('flood_time')}с)"
    )


@router.message(Command("floodmode"), IsAdminFilter())
async def cmd_floodmode(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if arg not in FLOOD_MODES:
        await message.reply("Режимы: " + ", ".join(FLOOD_MODES))
        return
    await update_settings(message.chat.id, flood_mode=arg)
    await message.reply(f"Режим антифлуда: {arg}")


@router.message(Command("setcaps"), IsAdminFilter())
async def cmd_setcaps(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setcaps 80 12 — процент и минимум букв")
        return
    a = command.args.split()
    try:
        await update_settings(message.chat.id, caps_percent=int(a[0]), caps_min=int(a[1]) if len(a) > 1 else 12)
        await message.reply("Настройки капса обновлены.")
    except Exception:
        await message.reply("Неверный формат.")
