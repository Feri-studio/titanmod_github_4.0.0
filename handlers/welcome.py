import random
import time
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery, ChatPermissions
from aiogram.filters import Command, CommandObject, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import fill_welcome, mention, html_esc
from core.defaults import JOIN_PLACEHOLDERS, EMOJI_CAPTCHA, CAPTCHA_MODES
from database.db import (
    ensure_chat, get_settings, update_settings, bump_stat, track_join,
    set_captcha, get_captcha, del_captcha, is_gbanned, is_fbanned, get_chat_fed,
    is_approved,
)
from keyboards.inline import captcha_kb
from handlers.common import MUTE_PERMS, FREE_PERMS
from services.logger import send_log

router = Router()


@router.message(Command("setwelcome"), IsAdminFilter(), IsGroupFilter())
async def cmd_setwelcome(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("Текст приветствия. Переменные:\n" + "\n".join(f"<code>{k}</code> — {v}" for k, v in JOIN_PLACEHOLDERS.items()))
        return
    await update_settings(message.chat.id, welcome_text=command.args, welcome_enabled=1)
    await message.reply("Приветствие обновлено.")


@router.message(Command("resetwelcome"), IsAdminFilter(), IsGroupFilter())
async def cmd_resetwelcome(message: Message):
    await update_settings(message.chat.id, welcome_text="Добро пожаловать, {user}!")
    await message.reply("Сброшено.")


@router.message(Command("welcome"), IsAdminFilter(), IsGroupFilter())
async def cmd_welcome(message: Message, command: CommandObject):
    s = await get_settings(message.chat.id)
    arg = (command.args or "").strip().lower()
    if arg in ("on", "off", "1", "0", "да", "нет"):
        on = arg in ("on", "1", "да")
        await update_settings(message.chat.id, welcome_enabled=1 if on else 0)
        await message.reply("Приветствия " + ("включены" if on else "выключены"))
        return
    await message.reply(
        f"Статус: {'вкл' if s.get('welcome_enabled') else 'выкл'}\n"
        f"Капча: {'вкл' if s.get('welcome_captcha') else 'выкл'} ({s.get('captcha_mode')})\n"
        f"Текст:\n{html_esc(s.get('welcome_text'))}"
    )


@router.message(Command("setgoodbye"), IsAdminFilter(), IsGroupFilter())
async def cmd_setgoodbye(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setgoodbye текст")
        return
    await update_settings(message.chat.id, goodbye_text=command.args, goodbye_enabled=1)
    await message.reply("Прощание обновлено.")


@router.message(Command("goodbye"), IsAdminFilter(), IsGroupFilter())
async def cmd_goodbye(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if arg in ("on", "off"):
        await update_settings(message.chat.id, goodbye_enabled=1 if arg == "on" else 0)
        await message.reply("Готово.")
        return
    s = await get_settings(message.chat.id)
    await message.reply(html_esc(s.get("goodbye_text") or "не задано"))


@router.message(Command("cleanwelcome"), IsAdminFilter(), IsGroupFilter())
async def cmd_cleanwelcome(message: Message, command: CommandObject):
    on = (command.args or "on").strip().lower() in ("on", "1", "да")
    await update_settings(message.chat.id, clean_welcome=1 if on else 0)
    await message.reply("cleanwelcome " + ("on" if on else "off"))


@router.message(Command("captcha"), IsAdminFilter(), IsGroupFilter())
async def cmd_captcha(message: Message, command: CommandObject):
    arg = (command.args or "on").strip().lower()
    on = arg in ("on", "1", "да", "yes")
    await update_settings(message.chat.id, welcome_captcha=1 if on else 0, welcome_mute=1 if on else 0)
    await message.reply("Капча " + ("включена" if on else "выключена"))


@router.message(Command("captchamode"), IsAdminFilter(), IsGroupFilter())
async def cmd_captchamode(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if arg not in CAPTCHA_MODES:
        await message.reply("Режимы: " + ", ".join(CAPTCHA_MODES))
        return
    await update_settings(message.chat.id, captcha_mode=arg)
    await message.reply(f"Режим капчи: {arg}")


@router.message(Command("captchatime"), IsAdminFilter(), IsGroupFilter())
async def cmd_captchatime(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/captchatime 120")
        return
    await update_settings(message.chat.id, captcha_timeout=int(command.args.strip()))
    await message.reply("Таймаут обновлён.")


@router.message(Command("setrules"), IsAdminFilter(), IsGroupFilter())
async def cmd_setrules(message: Message, command: CommandObject):
    from core.style import rules_card, ok, card
    if not command.args:
        s = await get_settings(message.chat.id)
        await message.reply(
            rules_card(message.chat.title or "чат", s.get("rules") or "")
        )
        return
    await update_settings(message.chat.id, rules=command.args.strip())
    await message.reply(ok("Правила сохранены. Показать: /rules"))


@router.message(Command("rules", "правила"))
async def cmd_rules(message: Message, bot: Bot):
    from core.style import rules_card, ok
    from database.db import get_connection
    chat_id = message.chat.id
    title = message.chat.title or "чат"
    if message.chat.type == "private":
        conn = await get_connection(message.from_user.id)
        if not conn:
            await message.reply(
                "📜 Открой /rules <b>в группе</b> или привяжи чат: <code>/connect</code>"
            )
            return
        chat_id = conn
        title = "привязанный чат"
    s = await get_settings(chat_id)
    text = rules_card(title, s.get("rules") or "")
    if s.get("private_rules") and message.chat.type != "private":
        try:
            await bot.send_message(message.from_user.id, text)
            await message.reply(ok("Правила отправлены в ЛС."))
            return
        except Exception:
            pass
    await message.reply(text)


@router.message(Command("privaterules"), IsAdminFilter(), IsGroupFilter())
async def cmd_privrules(message: Message, command: CommandObject):
    from core.style import ok
    on = (command.args or "on").lower() in ("on", "1", "да", "yes", "true")
    await update_settings(message.chat.id, private_rules=1 if on else 0)
    await message.reply(ok("Правила в ЛС: " + ("включены" if on else "выключены")))


@router.message(Command("clearrules"), IsAdminFilter(), IsGroupFilter())
async def cmd_clearrules(message: Message):
    from core.style import ok
    await update_settings(message.chat.id, rules="")
    await message.reply(ok("Правила очищены."))


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_join(event: ChatMemberUpdated, bot: Bot):
    chat = await ensure_chat(event.chat.id, event.chat.title, event.chat.type, event.chat.username)
    s = chat["settings"]
    user = event.new_chat_member.user
    if user.is_bot:
        if s.get("block_bots"):
            try:
                await bot.ban_chat_member(event.chat.id, user.id)
            except Exception:
                pass
        return

    g = await is_gbanned(user.id)
    if g and s.get("gban_enable", 1):
        try:
            await bot.ban_chat_member(event.chat.id, user.id)
            await send_log(bot, event.chat.id, "gban", f"Авто-gban {mention(user)}: {html_esc(g.get('reason'))}", user.id)
        except Exception:
            pass
        return

    fed = await get_chat_fed(event.chat.id)
    if fed:
        fb = await is_fbanned(fed["fed_id"], user.id)
        if fb:
            try:
                await bot.ban_chat_member(event.chat.id, user.id)
            except Exception:
                pass
            return

    await bump_stat(event.chat.id, "joins")
    joins = await track_join(event.chat.id, int(s.get("raid_window", 12) or 12))
    if s.get("raid_mode") or joins >= int(s.get("raid_joins", 10) or 10):
        action = s.get("raid_action", "mute")
        try:
            if action == "ban":
                await bot.ban_chat_member(event.chat.id, user.id)
            elif action == "kick":
                await bot.ban_chat_member(event.chat.id, user.id)
                await bot.unban_chat_member(event.chat.id, user.id)
            else:
                await bot.restrict_chat_member(event.chat.id, user.id, permissions=MUTE_PERMS)
            await send_log(bot, event.chat.id, "raid", f"Антирейд {action} для {mention(user)} (joins={joins})", user.id)
        except Exception:
            pass
        return

    count = 0
    try:
        count = await bot.get_chat_member_count(event.chat.id)
    except Exception:
        pass

    if s.get("welcome_captcha") and not await is_approved(event.chat.id, user.id):
        try:
            await bot.restrict_chat_member(event.chat.id, user.id, permissions=MUTE_PERMS)
        except Exception:
            pass
        mode = s.get("captcha_mode") or "button"
        timeout = int(s.get("captcha_timeout", 120) or 120)
        answer = "ok"
        payload = ""
        text = f"{mention(user)}, подтверди что ты человек."
        if mode == "math":
            a, b = random.randint(2, 9), random.randint(2, 9)
            answer = str(a + b)
            text = f"{mention(user)}, сколько будет {a}+{b}? Ответь числом в чат."
        elif mode == "emoji":
            correct = random.choice(EMOJI_CAPTCHA)
            others = random.sample([e for e in EMOJI_CAPTCHA if e != correct], 3)
            opts = others + [correct]
            random.shuffle(opts)
            answer = correct
            payload = "|".join(opts)
            text = f"{mention(user)}, нажми {correct}"
        kb = captcha_kb(event.chat.id, user.id, mode, payload)
        try:
            msg = await bot.send_message(event.chat.id, text, reply_markup=kb)
            await set_captcha(event.chat.id, user.id, answer, msg.message_id, time.time() + timeout)
        except Exception:
            pass
        return

    if not s.get("welcome_enabled", 1):
        return
    text = fill_welcome(s.get("welcome_text") or "Добро пожаловать, {user}!", user, event.chat, count, s.get("rules") or "")
    try:
        sent = await bot.send_message(event.chat.id, text, disable_web_page_preview=True)
        if s.get("clean_welcome") and s.get("last_welcome_id"):
            try:
                await bot.delete_message(event.chat.id, int(s["last_welcome_id"]))
            except Exception:
                pass
            await update_settings(event.chat.id, last_welcome_id=sent.message_id)
    except Exception:
        pass


@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_leave(event: ChatMemberUpdated, bot: Bot):
    s = (await ensure_chat(event.chat.id, event.chat.title))["settings"]
    await bump_stat(event.chat.id, "leaves")
    if not s.get("goodbye_enabled"):
        return
    user = event.old_chat_member.user
    text = fill_welcome(s.get("goodbye_text") or "{user} покинул чат.", user, event.chat)
    try:
        await bot.send_message(event.chat.id, text)
    except Exception:
        pass


@router.callback_query(F.data.startswith("cpt:"))
async def captcha_cb(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    _, answer, chat_id, user_id = parts[0], parts[1], int(parts[2]), int(parts[3])
    if callback.from_user.id != user_id:
        await callback.answer("Это не твоя капча", show_alert=True)
        return
    rec = await get_captcha(chat_id, user_id)
    if not rec:
        await callback.answer("Капча неактуальна")
        return
    if str(rec["answer"]) != str(answer) and not (rec["answer"] == "ok" and answer == "ok"):
        await callback.answer("Неверно", show_alert=True)
        return
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=FREE_PERMS)
    except Exception:
        pass
    await del_captcha(chat_id, user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Добро пожаловать!")
    s = await get_settings(chat_id)
    if s.get("welcome_enabled"):
        try:
            text = fill_welcome(s.get("welcome_text") or "Добро пожаловать, {user}!", callback.from_user, callback.message.chat)
            await bot.send_message(chat_id, text)
        except Exception:
            pass


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.regexp(r"^\d{1,3}$"))
async def captcha_math_answer(message: Message, bot: Bot):
    rec = await get_captcha(message.chat.id, message.from_user.id)
    if not rec:
        return
    if str(rec["answer"]) != (message.text or "").strip():
        return
    try:
        await bot.restrict_chat_member(message.chat.id, message.from_user.id, permissions=FREE_PERMS)
        await del_captcha(message.chat.id, message.from_user.id)
        await message.reply("Капча пройдена.")
        if rec.get("message_id"):
            try:
                await bot.delete_message(message.chat.id, rec["message_id"])
            except Exception:
                pass
    except Exception:
        pass
