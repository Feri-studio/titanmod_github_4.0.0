SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        title TEXT,
        chat_type TEXT,
        username TEXT,
        members INTEGER DEFAULT 0,
        settings TEXT DEFAULT '{}',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_bot INTEGER DEFAULT 0,
        lang TEXT,
        reputation INTEGER DEFAULT 0,
        gbanned INTEGER DEFAULT 0,
        gban_reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS punishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        type TEXT,
        reason TEXT,
        until_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        name TEXT,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        buttons TEXT,
        admin_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chat_id, name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS filters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        keyword TEXT,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        buttons TEXT,
        exact INTEGER DEFAULT 0,
        admin_id INTEGER,
        uses INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chat_id, keyword)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS badwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        word TEXT,
        UNIQUE(chat_id, word)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS whitelist_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        domain TEXT,
        UNIQUE(chat_id, domain)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS whitelist_users (
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS approved (
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS blacklist_stickers (
        chat_id INTEGER,
        file_unique TEXT,
        pack TEXT,
        PRIMARY KEY (chat_id, file_unique)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS federations (
        fed_id TEXT PRIMARY KEY,
        owner_id INTEGER,
        name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fed_chats (
        fed_id TEXT,
        chat_id INTEGER,
        PRIMARY KEY (fed_id, chat_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fed_admins (
        fed_id TEXT,
        user_id INTEGER,
        PRIMARY KEY (fed_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fed_bans (
        fed_id TEXT,
        user_id INTEGER,
        admin_id INTEGER,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (fed_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        target_id INTEGER,
        message_id INTEGER,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS connections (
        user_id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS captcha (
        chat_id INTEGER,
        user_id INTEGER,
        answer TEXT,
        message_id INTEGER,
        expires REAL,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS flood_tracker (
        chat_id INTEGER,
        user_id INTEGER,
        message_count INTEGER DEFAULT 1,
        first_message_time REAL,
        last_text TEXT,
        dup_count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS join_tracker (
        chat_id INTEGER PRIMARY KEY,
        joins INTEGER DEFAULT 0,
        window_start REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stats (
        chat_id INTEGER,
        date TEXT,
        messages INTEGER DEFAULT 0,
        joins INTEGER DEFAULT 0,
        leaves INTEGER DEFAULT 0,
        warns INTEGER DEFAULT 0,
        bans INTEGER DEFAULT 0,
        mutes INTEGER DEFAULT 0,
        kicks INTEGER DEFAULT 0,
        deleted INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reputation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        from_id INTEGER,
        to_id INTEGER,
        delta INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS afk (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        since TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        text TEXT,
        fire_at REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS disabled_commands (
        chat_id INTEGER,
        command TEXT,
        PRIMARY KEY (chat_id, command)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS custom_commands (
        chat_id INTEGER,
        command TEXT,
        content TEXT,
        PRIMARY KEY (chat_id, command)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS name_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        username TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gbans (
        user_id INTEGER PRIMARY KEY,
        admin_id INTEGER,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bot_chats (
        chat_id INTEGER PRIMARY KEY,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        event TEXT,
        payload TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_warns_user ON warns(chat_id, user_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_notes_chat ON notes(chat_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_filters_chat ON filters(chat_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_punish_user ON punishments(chat_id, user_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reminders_fire ON reminders(fire_at)
    """,
]
