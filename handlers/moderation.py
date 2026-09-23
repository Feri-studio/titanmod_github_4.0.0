"""Auto-moderation engine: locks, blacklist, links, channels, force-sub, filters, files."""
import os
from datetime import datetime, timedelta, timezone
from aiogram import Router, Bot, F
from aiogram.types import Message, ContentType
from aiogram.enums import ChatType
from core.permissions import admin_cache
from core.defaults import DEFAULT_BADWORDS
from core.text import extract_urls, mention, html_esc, looks_like_url_name, caps_ratio
from core.timeparse import is_night
from database.db import (
    get_settings, get_badwords, get_whitelist, is_approved, get_filters, bump_filter_use,
    bump_stat, is_bl_sticker, get_dup_count, get_custom_command, get_captcha,
    get_afk, clear_afk,
)
from services.locks import content_locked, parse_lock_set
from services.scoring import score_text, should_delete, should_punish, describe
from handlers.common import do_mute, MUTE_PERMS
from utils.media import send_saved
from utils.buttons import build_markup

router = Router()


async def _privileged(bot: Bot, message: Message) -> bool:
    if not message.from_user:
        return True
    if await admin_cache.is_admin(bot, message.chat.id, message.from_user.id):
        return True
    if await is_approved(message.chat.id, message.from_user.id):
        return True
    return False


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def auto_mod(message: Message, bot: Bot, settings: dict | None = None):
    if message.chat.type not in ("group", "supergroup"):
        return
    s = settings or await get_settings(message.chat.id)

    # daily message counter for /chatstats
    try:
        if message.from_user and not message.from_user.is_bot:
            await bump_stat(message.chat.id, "messages")
    except Exception:
        pass

    # custom commands
    if message.text and message.text.startswith("/"):
        cmd = message.text[1:].split()[0].split("@")[0].lower()
        content = await get_custom_command(message.chat.id, cmd)
        if content:
            await message.reply(content)
            return

    # AFK
    if message.from_user:
        me = await get_afk(message.from_user.id)
        if me and not (message.text and message.text.startswith("/afk")):
            await clear_afk(message.from_user.id)
            try:
                await message.reply(f"{mention(message.from_user)} снова с нами.")
            except Exception:
                pass
        targets = []
        if message.reply_to_message and message.reply_to_message.from_user:
            targets.append(message.reply_to_message.from_user)
        for e in message.entities or []:
            if e.type == "text_mention" and e.user:
                targets.append(e.user)
        for u in targets:
            rec = await get_afk(u.id)
            if rec:
                try:
                    await message.reply(f"{mention(u)} AFK: {html_esc(rec.get('reason') or '')}")
                except Exception:
                    pass

    # pending captcha users cannot talk except math answer handled elsewhere
    if message.from_user:
        cap = await get_captcha(message.chat.id, message.from_user.id)
        if cap and not (message.text and message.text.isdigit()):
            try:
                await message.delete()
            except Exception:
                pass
            return

    # service messages
    if s.get("auto_delete_service", 1) and message.content_type in {
        ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER, ContentType.PINNED_MESSAGE,
        ContentType.NEW_CHAT_TITLE, ContentType.NEW_CHAT_PHOTO, ContentType.DELETE_CHAT_PHOTO,
    }:
        try:
            await message.delete()
        except Exception:
            pass
        return

    if not message.from_user:
        return
    if await _privileged(bot, message):
        await _run_filters(message, bot, s)
        return

    # gban already handled on join; still skip

    # anti-channel (comments as channel)
    if s.get("anti_channel", 1) and message.sender_chat and message.sender_chat.id != message.chat.id:
        try:
            await message.delete()
            await bump_stat(message.chat.id, "deleted")
        except Exception:
            pass
        return

    # force subscribe (every message, skip admins/approved)
    if (
        s.get("force_sub")
        and s.get("force_sub_chat")
        and message.from_user
        and not message.from_user.is_bot
        and not await _privileged(bot, message)
    ):
        target = str(s["force_sub_chat"]).strip()
        try:
            ch = target if target.startswith("@") or target.startswith("-") else (
                int(target) if target.lstrip("-").isdigit() else ("@" + target.lstrip("@"))
            )
            mem = await bot.get_chat_member(ch, message.from_user.id)
            if mem.status in ("left", "kicked"):
                try:
                    await message.delete()
                except Exception:
                    pass
                try:
                    await bot.restrict_chat_member(
                        message.chat.id, message.from_user.id, permissions=MUTE_PERMS
                    )
                except Exception:
                    pass
                try:
                    await message.answer(
                        f"🔒 {mention(message.from_user)}, подпишись на "
                        f"<code>{html_esc(str(target))}</code>, чтобы писать в чат."
                    )
                except Exception:
                    pass
                try:
                    from services.logger import send_log
                    await send_log(
                        bot, message.chat.id, "force_sub",
                        f"Force-sub: {mention(message.from_user)} не подписан на {html_esc(str(target))}",
                        message.from_user.id, None,
                    )
                except Exception:
                    pass
                return
        except Exception:
            pass

    # night mode
    if s.get("nightmode") and is_night(datetime.now(timezone.utc), s.get("night_start") or "23:00", s.get("night_end") or "07:00"):
        try:
            await message.delete()
            await bump_stat(message.chat.id, "deleted")
        except Exception:
            pass
        return

    # username / name with url
    if s.get("block_names_urls") and message.from_user and looks_like_url_name(message.from_user.full_name or ""):
        try:
            await message.delete()
        except Exception:
            pass
        return

    text = (message.text or message.caption or "")
    text_l = text.lower()

    if s.get("antispam", 1) and text:
        scored = score_text(text, s)
        if should_punish(scored, int(s.get("spam_punish") or 75)):
            await _punish_delete(message, bot, s, "mute", describe(scored))
            return
        if should_delete(scored, int(s.get("spam_threshold") or 40)):
            await _punish_delete(message, bot, s, "delete", describe(scored))
            return

    # blacklist words
    if s.get("filter_badwords", 1) and text_l:
        extra = await get_badwords(message.chat.id)
        banned = set(DEFAULT_BADWORDS + extra)
        hit = next((w for w in banned if w and w in text_l), None)
        if hit:
            await _punish_delete(message, bot, s, s.get("blacklist_mode") or "delete", f"слово: {hit}")
            return

    # links
    if s.get("filter_links") and text:
        urls = extract_urls(text)
        if urls:
            white = await get_whitelist(message.chat.id)
            allowed = False
            if white:
                blob = " ".join(urls).lower()
                allowed = any(d in blob for d in white)
            if not allowed:
                await _punish_delete(message, bot, s, "delete", "ссылка")
                return

    # blocked extensions / size
    if message.document:
        name = (message.document.file_name or "").lower()
        ext = name.rsplit(".", 1)[-1] if "." in name else ""
        blocked = [x.strip() for x in str(s.get("blocked_ext") or "").split(",") if x.strip()]
        if ext in blocked:
            await _punish_delete(message, bot, s, "delete", "файл")
            return
        max_mb = int(s.get("max_file_mb") or 0)
        if max_mb and message.document.file_size and message.document.file_size > max_mb * 1024 * 1024:
            await _punish_delete(message, bot, s, "delete", "размер файла")
            return

    # stickers blacklist
    if message.sticker:
        if await is_bl_sticker(message.chat.id, message.sticker.file_unique_id):
            await _punish_delete(message, bot, s, "delete", "стикер")
            return

    # duplicates
    if s.get("duplicates") and text:
        dups = await get_dup_count(message.chat.id, message.from_user.id)
        if dups >= 3:
            await _punish_delete(message, bot, s, "mute", "дубли")
            return

    # locks
    locks = parse_lock_set(s.get("locks"))
    reason = content_locked(message, locks, s)
    if reason:
        try:
            await message.delete()
            await bump_stat(message.chat.id, "deleted")
            if s.get("lock_warn"):
                warn = await message.answer(f"{mention(message.from_user)}, это запрещено ({reason}).")
                try:
                    await warn.delete()
                except Exception:
                    pass
        except Exception:
            pass
        return

    # CAPS
    if text and len(text) >= int(s.get("caps_min") or 12) and caps_ratio(text) >= int(s.get("caps_percent") or 80):
        if "messages" in locks or s.get("filter_badwords"):
            # only if they locked messages-as-caps via high caps — optional delete
            pass

    await _run_filters(message, bot, s)


async def _run_filters(message: Message, bot: Bot, s: dict):
    if not s.get("filters_enabled", 1):
        return
    text = (message.text or message.caption or "")
    if not text:
        return
    low = text.lower()
    try:
        items = await get_filters(message.chat.id)
    except Exception:
        return
    for it in items:
        kw = (it.get("keyword") or "").lower()
        if not kw:
            continue
        hit = (kw == low) if it.get("exact") else (kw in low)
        if not hit:
            continue
        await bump_filter_use(it["id"])
        markup = build_markup(it.get("buttons"))
        try:
            await send_saved(
                bot, message.chat.id, it.get("content") or "",
                it.get("file_id"), it.get("file_type"), markup, message.message_id,
            )
        except Exception:
            pass
        break


async def _punish_delete(message: Message, bot: Bot, s: dict, mode: str, reason: str):
    try:
        await message.delete()
        await bump_stat(message.chat.id, "deleted")
    except Exception:
        pass
    uid = message.from_user.id
    try:
        if mode == "warn":
            from database.db import add_warn
            await add_warn(message.chat.id, uid, bot.id, reason)
        elif mode == "mute":
            until = datetime.now(timezone.utc) + timedelta(seconds=int(s.get("flood_time") or 300))
            await bot.restrict_chat_member(message.chat.id, uid, permissions=MUTE_PERMS, until_date=until)
        elif mode == "kick":
            await bot.ban_chat_member(message.chat.id, uid)
            await bot.unban_chat_member(message.chat.id, uid)
        elif mode == "ban":
            await bot.ban_chat_member(message.chat.id, uid)
    except Exception:
        pass
