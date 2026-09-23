"""Implement previously missing catalog commands — TitanMod 4.2+."""
from __future__ import annotations

import asyncio
import hashlib
import html
import random
import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject

from config import config
from core.style import card, ok, fail, HR
from core.text import html_esc, mention
from core.ranks import effective_rank, rank_badge, get_rank_info
from filters.rank import RankOrAdminFilter
from filters.admin import IsGroupFilter, IsAdminFilter
from database.db import get_settings, update_settings, bump_stat, get_stats
from database.extra import (
    get_balance, add_coins, get_user_rank, set_user_rank, list_ranks,
    check_cooldown, set_cooldown,
)
from handlers.common import resolve_user, ensure_can_act, do_ban, do_mute, do_unmute, MUTE_PERMS, FREE_PERMS
from services.message_cache import last_deleted, last_edited, mark_deleted

router = Router()

# ---------- SNIPЕ ----------
@router.message(Command("snipe"))
async def cmd_snipe(message: Message):
    if message.chat.type == "private":
        return
    cm = last_deleted(message.chat.id)
    if not cm:
        await message.reply("🗑 Нечего снайпить — удалений в кэше нет.\nБот видит только сообщения после запуска.")
        return
    await message.reply(
        card(
            "Snipe",
            f"От: <b>{html_esc(cm.full_name)}</b> (<code>{cm.user_id}</code>)\n"
            f"{HR}\n{html_esc(cm.text[:1500])}",
            emoji="🎯",
        )
    )


@router.message(Command("editsnipe"))
async def cmd_editsnipe(message: Message):
    if message.chat.type == "private":
        return
    cm = last_edited(message.chat.id)
    if not cm:
        await message.reply("✏️ Правок в кэше нет.")
        return
    await message.reply(
        card(
            "Edit snipe",
            f"От: <b>{html_esc(cm.full_name)}</b>\n"
            f"<b>Было:</b> {html_esc(cm.old_text[:700])}\n"
            f"<b>Стало:</b> {html_esc(cm.text[:700])}",
            emoji="✏️",
        )
    )


# ---------- ALIASES to existing systems ----------
@router.message(Command("tempban"), RankOrAdminFilter("ban"))
async def cmd_tempban(message: Message, bot: Bot, command: CommandObject):
    from handlers.punish import _ban
    await _ban(message, bot, command.args or "", silent=False, delete=False, force_time=True)


@router.message(Command("tempmute"), RankOrAdminFilter("mute"))
async def cmd_tempmute(message: Message, bot: Bot, command: CommandObject):
    # reuse mute with force time via punish if available
    args = (command.args or "").strip() or "1h"
    user, rest = await resolve_user(message, bot, args)
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    from core.timeparse import parse_time, format_time
    seconds = parse_time(rest.split()[0] if rest else "1h", 3600) or 3600
    until = datetime.utcnow() + timedelta(seconds=seconds)
    try:
        await do_mute(bot, message.chat.id, user.id, until=until)
        await message.reply(ok(f"Мут {mention(user)} на {format_time(seconds)}"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("softban"), RankOrAdminFilter("ban"))
async def cmd_softban(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    try:
        await do_ban(bot, message.chat.id, user.id)
        await bot.unban_chat_member(message.chat.id, user.id)
        await message.reply(ok(f"Softban {mention(user)} — кик + разбан (сообщения не чистятся API)."))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("warnlist"))
async def cmd_warnlist(message: Message, command: CommandObject, bot: Bot):
    # redirect logic inline
    from database.db import get_warns
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    rows = await get_warns(message.chat.id, user.id)
    if not rows:
        await message.reply(f"Варнов у {mention(user)} нет")
        return
    lines = [f"⚠ Варны {mention(user)}", HR]
    for r in rows[:15]:
        lines.append(f"• #{r.get('id')} {html_esc(str(r.get('reason') or '')[:80])}")
    await message.reply("\n".join(lines))


@router.message(Command("warnsreset"), RankOrAdminFilter("warn"))
async def cmd_warnsreset(message: Message, bot: Bot, command: CommandObject):
    from database.db import clear_warns
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя")
        return
    await clear_warns(message.chat.id, user.id)
    await message.reply(ok(f"Варны {mention(user)} сброшены"))


@router.message(Command("note", "addnote"))
async def cmd_note_alias(message: Message, command: CommandObject):
    await message.reply("Заметки: <code>/save имя текст</code> · <code>/get имя</code> · <code>/notes</code>")


@router.message(Command("rmnote"))
async def cmd_rmnote_alias(message: Message):
    await message.reply("Удаление: <code>/clear имя</code> или <code>/remove имя</code>")


@router.message(Command("rmfilter"))
async def cmd_rmfilter_alias(message: Message):
    await message.reply("Удаление фильтра: <code>/stop ключевое</code>")


# ---------- RANKS extras ----------
@router.message(Command("rankinfo"))
async def cmd_rankinfo(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    if message.chat.type == "private":
        await message.reply("В группе: /rankinfo")
        return
    lvl = await effective_rank(bot, message.chat.id, user.id)
    info = get_rank_info(lvl)
    perms = ", ".join(sorted(info.perms)[:20]) if "*" not in info.perms else "все (*)"
    await message.reply(
        card("Ранг", f"{mention(user)}\n{rank_badge(lvl)}\nПрава: {html_esc(perms)}", emoji="🏅")
    )


@router.message(Command("demoterank", "promoterank"), RankOrAdminFilter("promote_mod"))
async def cmd_promo_demo(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Ответь на сообщение или укажи id")
        return
    cur = await get_user_rank(message.chat.id, user.id)
    is_demo = (message.text or "").lower().lstrip("/").startswith("demo")
    new = max(0, cur - 1) if is_demo else min(7, max(cur + 1, 1))
    actor = await effective_rank(bot, message.chat.id, message.from_user.id)
    if new >= actor and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нельзя выдать ранг ≥ своего"))
        return
    await set_user_rank(message.chat.id, user.id, new, message.from_user.id)
    await message.reply(ok(f"{mention(user)} → {rank_badge(new)}"))


@router.message(Command("settitle", "title"), RankOrAdminFilter("promote_mod"))
async def cmd_settitle(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("<code>/settitle @user Титул</code> или ответом")
        return
    title = (rest or "").strip()[:64] or "Mod"
    try:
        await bot.set_chat_administrator_custom_title(message.chat.id, user.id, title)
        await message.reply(ok(f"Титул {mention(user)}: <b>{html_esc(title)}</b>"))
    except Exception as e:
        await message.reply(fail(f"Нужны права promote и цель уже админ TG. {html_esc(e)}"))


# ---------- MASS / SAFETY ----------
@router.message(Command("unbanall"), RankOrAdminFilter("ban"))
async def cmd_unbanall(message: Message, bot: Bot):
    await message.reply(
        "Telegram API не отдаёт полный список банов. "
        "Разбань по id: <code>/unban ID</code>"
    )


@router.message(Command("unmuteall"), RankOrAdminFilter("mute"))
async def cmd_unmuteall(message: Message, bot: Bot):
    await message.reply(
        "Массовый unmute без списка restricted невозможен через Bot API. "
        "Сними мут: <code>/unmute</code> ответом."
    )


@router.message(Command("nuke"), RankOrAdminFilter("purge"))
async def cmd_nuke(message: Message, bot: Bot, command: CommandObject):
    n = 50
    if command.args and command.args.strip().isdigit():
        n = min(100, int(command.args.strip()))
    await message.reply(fail(f"Опасная очистка: используй /purge {n} ответом на сообщение-якорь."))


@router.message(Command("freeze"), RankOrAdminFilter("mute"))
async def cmd_freeze(message: Message, bot: Bot):
    try:
        await bot.set_chat_permissions(message.chat.id, MUTE_PERMS)
        await update_settings(message.chat.id, locked_until=1)
        await message.reply(ok("Чат заморожен (участники не пишут). /unfreeze"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("unfreeze"), RankOrAdminFilter("mute"))
async def cmd_unfreeze(message: Message, bot: Bot):
    try:
        await bot.set_chat_permissions(message.chat.id, FREE_PERMS)
        await update_settings(message.chat.id, locked_until=0)
        await message.reply(ok("Чат разморожен."))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("tagall", "pingall"), RankOrAdminFilter("purge"))
async def cmd_tagall(message: Message, bot: Bot):
    await message.reply(
        "Массовый tagall ограничен Bot API (нет полного списка участников без admin rights + долгий скан). "
        "Используй список админов: /adminlist"
    )


@router.message(Command("voiceban", "imgban"), RankOrAdminFilter("mute"))
async def cmd_media_ban(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    try:
        await bot.restrict_chat_member(message.chat.id, user.id, permissions=perms)
        await message.reply(ok(f"Медиа-ограничение для {mention(user)}"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("unvoiceban"), RankOrAdminFilter("mute"))
async def cmd_unvoiceban(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя")
        return
    try:
        await do_unmute(bot, message.chat.id, user.id)
        await message.reply(ok(f"Ограничения сняты: {mention(user)}"))
    except Exception as e:
        await message.reply(fail(str(e)))


# ---------- SETTINGS toggles ----------
@router.message(Command("antiraid", "antispam", "verification", "night"), IsAdminFilter())
async def cmd_toggle_security(message: Message, command: CommandObject):
    raw = (message.text or "").split()[0].lstrip("/").split("@")[0].lower()
    arg = (command.args or "on").lower()
    on = arg in ("on", "1", "да", "true", "вкл")
    key = {
        "antiraid": "raid_mode",
        "antispam": "antispam",
        "verification": "welcome_captcha",
        "night": "nightmode",
    }.get(raw, raw)
    await update_settings(message.chat.id, **{key: 1 if on else 0})
    await message.reply(ok(f"{raw} → <b>{'on' if on else 'off'}</b>"))


@router.message(Command("autorole"), IsAdminFilter())
async def cmd_autorole(message: Message, command: CommandObject):
    await message.reply(
        "Автороли через бота ограничены: бот не может выдавать роли как Discord. "
        "Используй captcha/approve: /captcha on · /approve"
    )


@router.message(Command("logchannel"), IsAdminFilter())
async def cmd_logchannel(message: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if arg in ("off", "0", "нет"):
        await update_settings(message.chat.id, log_chat_id=None)
        await message.reply(ok("Лог-чат выключен"))
        return
    if arg.lstrip("-").isdigit():
        await update_settings(message.chat.id, log_chat_id=int(arg))
        await message.reply(ok(f"Лог-чат: <code>{arg}</code>"))
        return
    await message.reply("<code>/logchannel -100... (id чата для логов)</code> или /logchannel off")


@router.message(Command("admins", "updateadmins"))
async def cmd_admins(message: Message, bot: Bot):
    if message.chat.type == "private":
        return
    try:
        admins = await bot.get_chat_administrators(message.chat.id)
    except Exception as e:
        await message.reply(fail(str(e)))
        return
    lines = ["👮 <b>Админы</b>", HR]
    for a in admins:
        u = a.user
        if u.is_bot:
            continue
        lines.append(f"• {mention(u)} — <code>{a.status}</code>")
    await message.reply("\n".join(lines) or "пусто")


@router.message(Command("anonadmin"), IsAdminFilter())
async def cmd_anonadmin(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, anon_admin=1 if on else 0)
    await message.reply(ok(f"anonadmin → {'on' if on else 'off'} (учитывается где поддержано)"))


@router.message(Command("check"))
async def cmd_check(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    if message.chat.type == "private":
        await message.reply(f"ID: <code>{user.id}</code>")
        return
    try:
        m = await bot.get_chat_member(message.chat.id, user.id)
        status = m.status
    except Exception:
        status = "?"
    lvl = await effective_rank(bot, message.chat.id, user.id)
    bal = await get_balance(message.chat.id, user.id)
    await message.reply(
        card(
            "Check",
            f"{mention(user)}\nTG: <code>{status}</code>\n{rank_badge(lvl)}\n💰 {bal}",
            emoji="🔍",
        )
    )


@router.message(Command("clean"), RankOrAdminFilter("delete"))
async def cmd_clean(message: Message):
    await message.reply("Очистка: <code>/purge 10</code> ответом · <code>/cleanup</code>")


@router.message(Command("description"), IsAdminFilter())
async def cmd_description(message: Message, bot: Bot, command: CommandObject):
    text = (command.args or "").strip()
    if not text:
        await message.reply("<code>/description текст</code>")
        return
    try:
        await bot.set_chat_description(message.chat.id, text[:255])
        await message.reply(ok("Описание чата обновлено"))
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("pinlist"))
async def cmd_pinlist(message: Message, bot: Bot):
    try:
        chat = await bot.get_chat(message.chat.id)
        pin = getattr(chat, "pinned_message", None)
        if not pin:
            await message.reply("Закрепов нет (Bot API отдаёт только текущий pin).")
            return
        preview = (pin.text or pin.caption or f"#{pin.message_id}")[:200]
        await message.reply(f"📌 <code>{pin.message_id}</code>\n{html_esc(preview)}")
    except Exception as e:
        await message.reply(fail(str(e)))


# ---------- INFO extras ----------
@router.message(Command("avatar"))
async def cmd_avatar(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    try:
        photos = await bot.get_user_profile_photos(user.id, limit=1)
        if not photos.total_count:
            await message.reply("Нет аватара")
            return
        file_id = photos.photos[0][-1].file_id
        await message.reply_photo(file_id, caption=f"Аватар {mention(user)}")
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("idcard"))
async def cmd_idcard(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    await message.reply(
        card(
            "ID Card",
            f"Имя: {html_esc(user.full_name)}\n"
            f"Username: @{html_esc(user.username or '—')}\n"
            f"ID: <code>{user.id}</code>\n"
            f"Bot: {user.is_bot}",
            emoji="🪪",
        )
    )


@router.message(Command("joindate", "firstseen", "lastseen"))
async def cmd_seen(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    # from DB users table if available
    try:
        from database.db import get_connection
        import aiosqlite
        from database.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
            row = await cur.fetchone()
        if not row:
            await message.reply(f"{mention(user)} — нет записей в БД бота (ещё не писал).")
            return
        data = dict(row)
        await message.reply(
            card(
                "Seen",
                f"{mention(user)}\n"
                f"first/seen fields: <code>{html_esc(str(data.get('created_at') or data.get('first_seen') or '—'))}</code>\n"
                f"last: <code>{html_esc(str(data.get('last_seen') or '—'))}</code>",
                emoji="👁",
            )
        )
    except Exception as e:
        await message.reply(fail(str(e)))


@router.message(Command("active", "inactive"))
async def cmd_active(message: Message):
    if message.chat.type == "private":
        return
    rows = await get_stats(message.chat.id)
    msg = warns = bans = 0
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict):
                msg += int(r.get("messages") or 0)
                warns += int(r.get("warns") or 0)
                bans += int(r.get("bans") or 0)
    body = f"Сообщений (счётчик бота): <b>{msg}</b>\nВарны: {warns} · баны: {bans}"
    await message.reply(card("Активность чата", body, emoji="📊"))


@router.message(Command("wiki"))
async def cmd_wiki(message: Message, command: CommandObject):
    q = (command.args or "").strip()
    if not q:
        await message.reply("<code>/wiki запрос</code>")
        return
    import urllib.request
    import json
    url = (
        "https://ru.wikipedia.org/api/rest_v1/page/summary/"
        + quote(q.replace(" ", "_"))
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TitanMod/4.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        title = data.get("title") or q
        extract = data.get("extract") or "Нет описания"
        link = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        await message.reply(
            card(title, html_esc(extract[:1500]) + (f"\n\n{link}" if link else ""), emoji="📚")
        )
    except Exception:
        await message.reply(fail("Википедия не ответила. Уточни запрос."))


@router.message(Command("weather"))
async def cmd_weather(message: Message, command: CommandObject):
    city = (command.args or "").strip()
    if not city:
        await message.reply("<code>/weather Москва</code>")
        return
    import urllib.request
    import json
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}&count=1&language=ru"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "TitanMod/4.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            geo = json.loads(resp.read().decode())
        results = geo.get("results") or []
        if not results:
            await message.reply(fail("Город не найден"))
            return
        lat, lon = results[0]["latitude"], results[0]["longitude"]
        name = results[0].get("name", city)
        wurl = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(urllib.request.Request(wurl, headers={"User-Agent": "TitanMod/4.2"}), timeout=8) as resp:
            w = json.loads(resp.read().decode())
        cw = w.get("current_weather") or {}
        await message.reply(
            card(
                f"Погода · {html_esc(name)}",
                f"🌡 <b>{cw.get('temperature', '?')}°C</b>\n"
                f"💨 Ветер: {cw.get('windspeed', '?')} км/ч\n"
                f"Код: {cw.get('weathercode', '?')}",
                emoji="🌤",
            )
        )
    except Exception:
        await message.reply(fail("Сервис погоды недоступен"))


@router.message(Command("translate"))
async def cmd_translate(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or ""
    if not text:
        await message.reply("<code>/translate текст</code> (простой EN⇄RU словарь-заглушка)")
        return
    # lightweight demo without API key
    await message.reply(
        card(
            "Translate",
            f"Исходный текст ({len(text)} симв.):\n{html_esc(text[:800])}\n\n"
            f"<i>Полный машинный перевод требует API-ключа. "
            f"Текст принят; для продакшена подключи LibreTranslate/Google.</i>",
            emoji="🌐",
        )
    )


@router.message(Command("qr"))
async def cmd_qr(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text:
        await message.reply("<code>/qr текст</code>")
        return
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote(text[:500])}"
    try:
        await message.reply_photo(url, caption=html_esc(text[:200]))
    except Exception:
        await message.reply(f"QR: {url}")


@router.message(Command("short"))
async def cmd_short(message: Message, command: CommandObject):
    url = (command.args or "").strip()
    if not url.startswith("http"):
        await message.reply("<code>/short https://...</code>")
        return
    # no external shortener without key — show hash token
    token = hashlib.md5(url.encode()).hexdigest()[:8]
    await message.reply(card("Short", f"Токен: <code>{token}</code>\nURL: {html_esc(url[:300])}\n<i>Локальная метка (без внешнего shortener)</i>", emoji="🔗"))


@router.message(Command("paste"))
async def cmd_paste(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or ""
    if not text:
        await message.reply("<code>/paste текст</code>")
        return
    await message.reply(f"<pre>{html_esc(text[:3500])}</pre>")


@router.message(Command("urban"))
async def cmd_urban(message: Message, command: CommandObject):
    q = (command.args or "").strip()
    if not q:
        await message.reply("<code>/urban word</code>")
        return
    import urllib.request
    import json
    try:
        url = f"https://api.urbandictionary.com/v0/define?term={quote(q)}"
        req = urllib.request.Request(url, headers={"User-Agent": "TitanMod/4.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        defs = data.get("list") or []
        if not defs:
            await message.reply(fail("Нет определения"))
            return
        d = defs[0]
        await message.reply(
            card(
                d.get("word") or q,
                html_esc((d.get("definition") or "")[:1200]),
                emoji="📖",
            )
        )
    except Exception:
        await message.reply(fail("Urban Dictionary недоступен"))


@router.message(Command("waifu", "neko"))
async def cmd_waifu(message: Message):
    import urllib.request
    import json
    kind = "neko" if "neko" in (message.text or "") else "waifu"
    try:
        url = f"https://api.waifu.pics/sfw/{kind}"
        req = urllib.request.Request(url, headers={"User-Agent": "TitanMod/4.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        img = data.get("url")
        if img:
            await message.reply_photo(img)
        else:
            await message.reply(fail("Нет картинки"))
    except Exception:
        await message.reply(fail("waifu.pics недоступен"))


@router.message(Command("meme"))
async def cmd_meme(message: Message):
    templates = ["Когда снова /ban", "Это не баг, а фича", "Админ спит, чат горит", "Purge 100"]
    await message.reply(card("Meme", random.choice(templates), emoji="😂"))


@router.message(Command("ascii", "figlet"))
async def cmd_ascii(message: Message, command: CommandObject):
    text = (command.args or "TITAN").strip()[:12]
    art = "\n".join("#" * (len(text) + 4) for _ in range(3))
    await message.reply(f"<pre>{html_esc(text)}\n{art}</pre>")


@router.message(Command("insult"))
async def cmd_insult(message: Message):
    lines = [
        "Ты как /warn без причины.",
        "Даже капча тебя не спасёт.",
        "Твой код — сплошной stub.",
    ]
    await message.reply(random.choice(lines))


@router.message(Command("shipname"))
async def cmd_shipname(message: Message, command: CommandObject):
    parts = (command.args or "").split()
    if len(parts) < 2 and message.reply_to_message and message.reply_to_message.from_user:
        a = message.from_user.first_name
        b = message.reply_to_message.from_user.first_name
    elif len(parts) >= 2:
        a, b = parts[0], parts[1]
    else:
        await message.reply("<code>/shipname Имя1 Имя2</code>")
        return
    ship = (a[: max(2, len(a)//2)] + b[len(b)//2 :]).title()
    score = int(hashlib.md5(f"{a}{b}".encode()).hexdigest()[:4], 16) % 101
    await message.reply(card("Ship", f"{html_esc(a)} + {html_esc(b)} = <b>{html_esc(ship)}</b>\n❤️ {score}%", emoji="💘"))


@router.message(Command("stopwatch"))
async def cmd_stopwatch(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    key = (message.chat.id, message.from_user.id)
    if not hasattr(cmd_stopwatch, "_t"):
        cmd_stopwatch._t = {}
    if arg in ("start", "on", ""):
        cmd_stopwatch._t[key] = time.time()
        await message.reply("⏱ Старт. Остановить: <code>/stopwatch stop</code>")
        return
    if arg in ("stop", "end"):
        t0 = cmd_stopwatch._t.pop(key, None)
        if not t0:
            await message.reply("Сначала /stopwatch start")
            return
        await message.reply(ok(f"Время: <b>{time.time() - t0:.1f}</b> сек"))


@router.message(Command("trigger"))
async def cmd_trigger(message: Message):
    await message.reply("Триггеры = фильтры: <code>/filter слово ответ</code>")


@router.message(Command("removecoins"), RankOrAdminFilter("settings"))
async def cmd_removecoins(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("<code>/removecoins @user 50</code>")
        return
    parts = (rest or "").split()
    if not parts or not parts[0].lstrip("-").isdigit():
        await message.reply("Укажи сумму")
        return
    amount = abs(int(parts[0]))
    bal = await add_coins(message.chat.id, user.id, -amount)
    await message.reply(ok(f"Снято {amount} с {mention(user)}. Баланс: <b>{bal}</b>"))


# ---------- FED extras ----------
@router.message(Command("fbanlist", "fedstat"))
async def cmd_fed_extra(message: Message):
    s = await get_settings(message.chat.id)
    fed = s.get("federation_id") or "—"
    await message.reply(
        card(
            "Federation",
            f"Fed ID: <code>{html_esc(str(fed))}</code>\n"
            f"Команды: /newfed /joinfed /fban /funban /feds",
            emoji="🕸",
        )
    )
