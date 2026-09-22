# TitanMod 4.5

Telegram-бот модерации на **aiogram 3** + **SQLite**: баны, варны, замки, ранги, экономика, тикеты, личный кабинет.

## За 5 минут

### 1. Токен
1. Открой [@BotFather](https://t.me/BotFather) → `/newbot` → скопируй токен.
2. Узнай свой id: [@userinfobot](https://t.me/userinfobot).

### 2. Настройка
```bash
cd titanmod_github
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Файл `.env`:
```env
BOT_TOKEN=123456:ABCDEF...
BOT_ADMINS=123456789
# опционально:
# DB_PATH=data/moderation_bot.db
# LOG_LEVEL=INFO
```

### 3. Запуск
```bash
python bot.py
```

Или Docker:
```bash
docker compose up -d --build
```
Данные БД: том `./data` → `data/moderation_bot.db`.

### 4. Группа (обязательно)
1. Добавь бота в группу / супергруппу.
2. Сделай **администратором** с правами:
   - удаление сообщений;
   - блокировка пользователей;
   - ограничение участников.
3. Напиши в группе `/start` или `/settings`.

Без прав админа команды `/ban` `/mute` `/freeze` **не смогут** выполниться (это лимит Telegram, не баг кода).

## Что умеет

| Раздел | Примеры |
|--------|---------|
| Наказания | `/ban` `/tban` `/mute` `/kick` `/warn` |
| Правила | `/setrules` `/rules` |
| Ранги 0–7 | `/setrank` `/myrank` `/stafflist` |
| Экономика | `/daily` `/work` `/shop` `/pay` |
| Тикеты | `/ticket` `/reply` `/close` |
| ЛС-кабинет | `/menu` |
| Утилиты | `/wiki` `/weather` `/snipe` `/qr` |
| 4.5 | `/preset` `/rep` `/schedule` `/siege` `/forcesub` `/inventory` |

Полный список **только реально подключённых** команд: `/commands`.

## Ранги

Штат бота (параллельно с Telegram-админами):

- 0 member → 7 owner  
- Права на `/ban` `/mute` и т.д. задаются уровнем ранга **или** статусом TG-админа.  
- Нельзя наказать равный/более высокий ранг.

## Бэкап

```bash
cp data/moderation_bot.db data/backup-$(date +%F).db
```

В Docker копируй `./data/`.

## Частые проблемы

| Симптом | Что сделать |
|---------|-------------|
| «Нет BOT_TOKEN» | Заполни `.env` |
| Бан/мут не работает | Выдай боту права админа в чате |
| Snipe пустой | Бот видит только сообщения после своего запуска |
| tagall / unbanall | Ограничение Bot API — смотри ответ бота |
| Рестарт сбросил snipe | Кэш в RAM, это нормально |

## Разработка

```bash
python -m pytest tests/ -q
```

Версия: файл `VERSION` (сейчас 4.5.0).

## Структура

```
bot.py              — точка входа
config.py           — env
handlers/           — команды
database/           — SQLite
core/               — ranks, style, commands catalog
middlewares/        — flood, context, snipe track
data/               — moderation_bot.db
```
