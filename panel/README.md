# TitanMod Web Panel

Админ-панель к той же SQLite, что и бот.

## Активация панели (как включить)

### 1. Зависимости
```bash
cd titanmod_github
pip install -r requirements.txt
```

### 2. Пароль в `.env`
```env
BOT_TOKEN=...              # как у бота
BOT_ADMINS=7975091645
ACTIVATE_CODE=7975091645
DB_PATH=data/moderation_bot.db
PANEL_PASSWORD=твой_пароль_панели
```

Если `PANEL_PASSWORD` не задан — для входа на сайт используется `ACTIVATE_CODE`.

### 3. Запуск
```bash
# терминал 1 — бот
python bot.py

# терминал 2 — панель
uvicorn panel.main:app --host 127.0.0.1 --port 8080
```

### 4. Браузер
Открой: **http://127.0.0.1:8080**  
Введи пароль → дашборд.

На VPS лучше не светить `0.0.0.0` без nginx/HTTPS/VPN.

## Активация группы (бот)

1. Добавь бота в группу, сделай админом.  
2. В группе (с аккаунта из `BOT_ADMINS`):
   ```text
   /activate 7975091645
   ```
3. Или в панели: **Чаты → открыть чат → Activate**.

## Разделы панели

Дашборд, чаты (JSON + флаги), поиск user, варны, наказания, gban, ранги, тикеты, экономика, notes, filters, badwords, feds, reports, modstats, events, xp, rep, inventory, schedule, marriages, disabled, approved, quarantine, config, download DB.
