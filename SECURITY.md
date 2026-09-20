# Security

- **Never commit** `.env` or a live bot token.
- If a token leaked (chat, screenshot, old commit) — revoke it in [@BotFather](https://t.me/BotFather) → your bot → API Token → Revoke.
- `BOT_ADMINS` are the only accounts that can `/gban` and `/broadcast`. Keep the list short.
- The SQLite file `data/moderation_bot.db` contains chat ids, warns and notes — do not publish it.
