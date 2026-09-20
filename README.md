# TitanMod

Модерационный бот для Telegram. Python 3.10+ · aiogram 3 · SQLite · **v3.1.0**

Групповой бот уровня Rose/GroupHelp: наказания, варны, 40+ замков контента, капча, антирейд, федерации, заметки, автоответы, логи, ночной режим, force-sub, XP, розыгрыши.

## Загрузить с GitHub

```bash
git clone https://github.com/YOUR_USERNAME/titanmod.git
cd titanmod
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Открой `.env` и вставь:

- `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `BOT_ADMINS` — твой Telegram id (узнать: [@userinfobot](https://t.me/userinfobot))

```bash
python bot.py
```

Добавь бота в группу **админом** (удаление сообщений + блокировка пользователей) и напиши `/commands`.

### Docker

```bash
cp .env.example .env   # заполни токен
docker compose up -d --build
```

## Как выложить этот проект на GitHub

1. На [github.com/new](https://github.com/new) создай репозиторий (например `titanmod`). **Не** добавляй README/License — они уже в проекте.
2. В папке бота:

```bash
git init
git add .
git commit -m "Initial commit: TitanMod"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/titanmod.git
git push -u origin main
```

Либо через GitHub CLI:

```bash
gh repo create titanmod --public --source=. --remote=origin --push
```

**Не пушь `.env`.** Токен только локально. Если токен уже светился в чате — сразу Revoke в BotFather.

CI (GitHub Actions) прогонит compile + тесты на Python 3.10–3.12 при каждом push.

## Быстрый старт (без git)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Возможности (модули)

| Модуль | Команды (часть) |
|--------|-----------------|
| Наказания | `/ban` `/tban` `/sban` `/dban` `/unban` `/kick` `/dkick` `/mute` `/tmute` `/smute` `/unmute` `/ro` `/rw` |
| Варны | `/warn` `/dwarn` `/unwarn` `/warns` `/resetwarns` `/setwarnlimit` `/warnmode` |
| Замки | `/lock` `/unlock` `/locks` `/locktypes` + 40 типов |
| Антифлуд | `/setflood` `/flood` `/floodmode` `/setfloodtime` |
| ЧС / БС | `/addbadword` `/badwords` `/blacklistmode` `/addwhite` `/whitelist` `/blsticker` |
| Вход | `/setwelcome` `/welcome` `/setgoodbye` `/captcha` `/captchamode` `/captchatime` |
| Правила | `/setrules` `/rules` `/privaterules` |
| Заметки | `/save` `/get` `/notes` `/clear` `#имя` кнопки `&&` |
| Фильтры | `/filter` `/stop` `/filters` `/stopall` |
| Федерации | `/newfed` `/joinfed` `/fban` `/unfban` `/fedinfo` `/fpromote` |
| Безопасность | `/raid` `/setraid` `/forcesub` `/antichannel` `/nightmode` `/lockdown` `/approve` `/report` |
| Админка | `/promote` `/demote` `/adminlist` `/pin` `/purge` `/del` `/settings` `/export` |
| Связь ЛС | `/connect` `/disconnect` `/connectid` `/connection` |
| Инфо | `/id` `/info` `/ginfo` `/history` `/punishments` `/stats` `/usernote` |
| Утилиты | `/ping` `/uptime` `/afk` `/remind` `/rep` `/calc` `/hash` `/tr` `/commands` |
| Fun | `/coin` `/joke` `/ship` `/hug` `/mock` … выкл в `/settings` |
| Владелец бота | `/gban` `/ungban` `/chatlist` `/broadcast` `/leave` `/botstats` |
| Форум | `/newtopic` `/closetopic` `/reopentopic` `/renametopic` `/deletetopic` |
| Файлы | `/maxfile` `/blockext` `/fileid` |
| XP | `/xp` `/rank` `/toplevel` `/setxp` `/xprate` |
| Розыгрыши | `/gstart 1h 1 приз` `/gend` |
| Карантин | `/quarantine` `/unquarantine` `/watch` `/watching` |
| Бэкап | `/backup` `/importbackup` `/dumpsettings` |
| Алиасы | `/addalias` `/aliases` |
| Массовые | `/muteall` `/unmuteallchat` |

Полный список: `/commands` и `/help`. Каталог в `core/commands.py`.

## Замки (`/locktypes`)

`messages media photo video audio voice video_note document sticker gif url forwards forwards_channel games inline poll location contact dice premium spoiler hashtag mention cashtag command rtl zalgo cyrillic latin arabic chinese emoji button invoice invite email phone tg channel bots via caption entities quote all`

Пример: `/lock url` запрещает ссылки обычным участникам. Админы и `/approve` пользователи не фильтруются.

## Приветствие — переменные

`{user}` `{name}` `{first}` `{last}` `{chat}` `{id}` `{username}` `{count}` `{date}` `{rules}`

Капча: `button` (кнопка), `math` (пример в чат), `emoji` (нажать нужный). Истёкшие капчи кикаются планировщиком.

## Заметки и кнопки

```
/save hello Привет && Сайт=https://example.com && Чат=https://t.me/xxx
```

Вызов: `#hello` или `/get hello`.

## Лицензия

MIT. См. [LICENSE](LICENSE) и [SECURITY.md](SECURITY.md).
