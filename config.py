import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> list[int]:
    ids = []
    for part in (raw or "").split(","):
        part = part.strip()
        if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
            ids.append(int(part))
    return ids


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMINS: list[int] = field(default_factory=lambda: _parse_ids(os.getenv("BOT_ADMINS", "")))
    DB_PATH: str = os.getenv("DB_PATH", "data/moderation_bot.db")
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "ru")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CAPTCHA_TTL: int = int(os.getenv("CAPTCHA_TTL", "120"))
    RAID_JOINS: int = int(os.getenv("RAID_JOINS", "10"))
    RAID_WINDOW: int = int(os.getenv("RAID_WINDOW", "12"))
    MAX_WARNS_HARD: int = 50
    MAX_NOTE_LENGTH: int = 4000
    MAX_FILTER_LENGTH: int = 4000
    MAX_WELCOME_LENGTH: int = 2000
    SCHEDULER_TICK: int = 20
    VERSION: str = "3.1.0"
    BOT_NAME: str = "TitanMod"

    def is_owner(self, user_id: int) -> bool:
        return user_id in self.ADMINS


config = Config()
