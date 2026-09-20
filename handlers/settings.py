from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from filters.admin import IsAdminFilter, IsGroupFilter
from core.style import HR, safe_edit
from core.text import html_esc
from core.defaults import LOCK_TYPES
from database.db import ensure_chat, get_chat, update_settings, get_settings, get_stats, get_badwords, get_whitelist
from keyboards.inline import settings_main_kb, toggle_kb, locks_kb, back_kb
from services.locks import parse_lock_set, dump_lock_set

router = Router()


@router.message(Command("settings", "настройки"), IsAdminFilter(), IsGroupFilter())
async def cmd_settings(message: Message):
    await ensure_chat(message.chat.id, message.chat.title)
    await message.reply(
        f"⚙️ <b>Настройки</b>\n{html_esc(message.chat.title)}\n{HR}\nВыбери раздел — всё кликабельно.",
        reply_markup=settings_main_kb(message.chat.id),
    )


@router.callback_query(F.data.startswith("set:"))
async def settings_cb(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    if action == "close":
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer("Закрыто")
        return
    chat_id = int(parts[2]) if len(parts) > 2 else callback.message.chat.id
    chat = await get_chat(chat_id) or await ensure_chat(chat_id)
    s = chat["settings"]
    page = int(parts[3]) if len(parts) > 3 else 0

    if action == "main":
        await safe_edit(callback.message, f"⚙️ <b>Настройки чата</b>\n{HR}", settings_main_kb(chat_id))
    elif action == "welcome":
        text = (
            f"Приветствия: {'ON' if s.get('welcome_enabled') else 'OFF'}\n"
            f"Капча: {'ON' if s.get('welcome_captcha') else 'OFF'} ({s.get('captcha_mode')})\n"
            f"Прощания: {'ON' if s.get('goodbye_enabled') else 'OFF'}\n"
            f"Текст:\n<code>{html_esc((s.get('welcome_text') or '')[:400])}</code>"
        )
        await callback.message.edit_text(
            text,
            reply_markup=toggle_kb(chat_id, [
                ("welcome_enabled", "Welcome", bool(s.get("welcome_enabled"))),
                ("goodbye_enabled", "Goodbye", bool(s.get("goodbye_enabled"))),
                ("welcome_captcha", "Captcha", bool(s.get("welcome_captcha"))),
                ("clean_welcome", "Clean", bool(s.get("clean_welcome"))),
                ("private_rules", "PM rules", bool(s.get("private_rules"))),
            ]),
        )
    elif action == "moderation":
        await callback.message.edit_text(
            "Фильтры модерации",
            reply_markup=toggle_kb(chat_id, [
                ("filter_badwords", "Мат", bool(s.get("filter_badwords"))),
                ("filter_links", "Ссылки", bool(s.get("filter_links"))),
                ("filter_forwards", "Репосты", bool(s.get("filter_forwards"))),
                ("filter_media", "Медиа", bool(s.get("filter_media"))),
                ("anti_channel", "Каналы", bool(s.get("anti_channel"))),
                ("auto_delete_service", "Служебные", bool(s.get("auto_delete_service"))),
                ("block_bots", "Боты", bool(s.get("block_bots"))),
                ("duplicates", "Дубли", bool(s.get("duplicates"))),
                ("gban_enable", "Gban", bool(s.get("gban_enable"))),
            ]),
        )
    elif action == "flood":
        await callback.message.edit_text(
            f"Антифлуд {s.get('flood_limit')}/{s.get('flood_period')}с режим {s.get('flood_mode')}",
            reply_markup=toggle_kb(chat_id, [
                ("antiflood", "Antiflood", bool(s.get("antiflood"))),
            ]),
        )
    elif action == "warns":
        await callback.message.edit_text(
            f"Лимит варнов: {s.get('warn_limit')}\nРежим: {s.get('warn_mode')}",
            reply_markup=back_kb(chat_id),
        )
    elif action == "locks":
        enabled = parse_lock_set(s.get("locks"))
        await callback.message.edit_text(
            f"Замки ({len(enabled)}/{len(LOCK_TYPES)})",
            reply_markup=locks_kb(chat_id, enabled, page),
        )
    elif action == "filters":
        words = await get_badwords(chat_id)
        white = await get_whitelist(chat_id)
        await callback.message.edit_text(
            f"Слов в ЧС: {len(words)}\nБелых доменов: {len(white)}\n"
            f"/addbadword /addwhite /filters /notes",
            reply_markup=back_kb(chat_id),
        )
    elif action == "security":
        await callback.message.edit_text(
            f"Капча {s.get('captcha_mode')} / {s.get('captcha_timeout')}с\n"
            f"Рейд: {'ON' if s.get('raid_mode') else 'OFF'} {s.get('raid_joins')}/{s.get('raid_window')}с\n"
            f"Force-sub: {s.get('force_sub_chat') or 'нет'}",
            reply_markup=toggle_kb(chat_id, [
                ("welcome_captcha", "Captcha", bool(s.get("welcome_captcha"))),
                ("raid_mode", "Raid", bool(s.get("raid_mode"))),
                ("force_sub", "ForceSub", bool(s.get("force_sub"))),
                ("anti_channel", "AntiCH", bool(s.get("anti_channel"))),
                ("reports", "Reports", bool(s.get("reports"))),
            ]),
        )
    elif action == "logs":
        await callback.message.edit_text(
            f"Лог-чат: <code>{s.get('log_chat_id') or 'нет'}</code>\n/setlog id",
            reply_markup=back_kb(chat_id),
        )
    elif action == "rules":
        await callback.message.edit_text(
            s.get("rules") or "Правил нет. /setrules",
            reply_markup=back_kb(chat_id),
        )
    elif action == "stats":
        rows = await get_stats(chat_id, 7)
        if not rows:
            text = "Пока нет данных."
        else:
            text = "Статистика (7 дней):\n"
            for r in rows:
                text += f"{r['date']}: msg {r['messages']} join {r['joins']} ban {r['bans']} warn {r['warns']}\n"
        await callback.message.edit_text(text, reply_markup=back_kb(chat_id))
    elif action == "night":
        await callback.message.edit_text(
            f"Ночь: {s.get('night_start')}–{s.get('night_end')} {'ON' if s.get('nightmode') else 'OFF'}",
            reply_markup=toggle_kb(chat_id, [("nightmode", "Night", bool(s.get("nightmode")))]),
        )
    elif action == "extra":
        await callback.message.edit_text(
            "Дополнительно",
            reply_markup=toggle_kb(chat_id, [
                ("fun_enabled", "Fun", bool(s.get("fun_enabled"))),
                ("reputation", "Rep", bool(s.get("reputation"))),
                ("afk_enabled", "AFK", bool(s.get("afk_enabled"))),
                ("filters_enabled", "Auto-filters", bool(s.get("filters_enabled"))),
                ("anon_admin", "Anon admin", bool(s.get("anon_admin"))),
            ]),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tg:"))
async def toggle_cb(callback: CallbackQuery):
    _, key, chat_id = callback.data.split(":")
    chat_id = int(chat_id)
    s = await get_settings(chat_id)
    new = 0 if s.get(key) else 1
    await update_settings(chat_id, **{key: new})
    await callback.answer("ON" if new else "OFF")
    callback.data = f"set:main:{chat_id}"
    # refresh main for simplicity
    await callback.message.edit_reply_markup(reply_markup=settings_main_kb(chat_id))


@router.callback_query(F.data.startswith("lockt:"))
async def lock_toggle(callback: CallbackQuery):
    _, key, chat_id = callback.data.split(":")
    chat_id = int(chat_id)
    s = await get_settings(chat_id)
    enabled = parse_lock_set(s.get("locks"))
    if key in enabled:
        enabled.discard(key)
        state = "OFF"
    else:
        enabled.add(key)
        state = "ON"
    await update_settings(chat_id, locks=dump_lock_set(enabled))
    await callback.answer(f"{key} {state}")
    await callback.message.edit_reply_markup(reply_markup=locks_kb(chat_id, enabled, 0))
