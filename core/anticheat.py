"""Anti-cheat / anti-abuse limits for TitanMod."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

# Economy caps (per action)
MAX_PAY = 50_000
MAX_COINFLIP = 5_000
MAX_DAILY_BET_TOTAL = 25_000  # sum of coinflip bets per user/chat/day
MAX_ROB_PERCENT = 0.2  # max 20% of victim balance
MIN_ROB_VICTIM = 20
MAX_CMD_ARGS_LEN = 800
MAX_TEXT_CMD_LEN = 1200

# Rate: command category → (max hits, window seconds)
CATEGORY_LIMITS = {
    "economy": (8, 60),
    "punish": (12, 60),
    "fun": (15, 30),
    "default": (20, 30),
}

ECONOMY_CMDS = frozenset({
    "daily", "pay", "transfer", "work", "crime", "slots", "rob", "coinflip",
    "flip", "buy", "shop", "givecoins", "addcoins", "removecoins", "setcoins",
})
PUNISH_CMDS = frozenset({
    "ban", "mute", "kick", "warn", "tban", "tmute", "purge", "dban", "sban",
})


@dataclass
class ACResult:
    ok: bool
    reason: str = ""


class AntiCheatEngine:
    def __init__(self) -> None:
        self._hits: dict[tuple, list[float]] = defaultdict(list)
        self._day_bets: dict[tuple, int] = defaultdict(int)
        self._day_key: str = ""
        self._flags: dict[int, int] = defaultdict(int)  # user_id → suspicion score

    def _prune(self, key: tuple, window: float, now: float) -> list[float]:
        arr = [t for t in self._hits[key] if now - t < window]
        self._hits[key] = arr
        return arr

    def check_command_rate(self, user_id: int, cmd: str) -> ACResult:
        if cmd in ECONOMY_CMDS:
            lim, win = CATEGORY_LIMITS["economy"]
            cat = "economy"
        elif cmd in PUNISH_CMDS:
            lim, win = CATEGORY_LIMITS["punish"]
            cat = "punish"
        else:
            lim, win = CATEGORY_LIMITS["default"]
            cat = "default"
        now = time.monotonic()
        key = (user_id, cat)
        arr = self._prune(key, win, now)
        if len(arr) >= lim:
            self._flags[user_id] += 1
            return ACResult(False, f"Слишком часто ({cat}). Подожди {int(win)}с.")
        arr.append(now)
        self._hits[key] = arr
        return ACResult(True)

    def check_pay(self, amount: int) -> ACResult:
        if amount <= 0:
            return ACResult(False, "Сумма должна быть > 0")
        if amount > MAX_PAY:
            return ACResult(False, f"Лимит перевода: {MAX_PAY} за раз")
        return ACResult(True)

    def check_coinflip(self, chat_id: int, user_id: int, bet: int) -> ACResult:
        if bet <= 0:
            return ACResult(False, "Ставка > 0")
        if bet > MAX_COINFLIP:
            return ACResult(False, f"Макс. ставка: {MAX_COINFLIP}")
        from datetime import date
        day = date.today().isoformat()
        if day != self._day_key:
            self._day_bets.clear()
            self._day_key = day
        key = (chat_id, user_id, day)
        total = self._day_bets[key] + bet
        if total > MAX_DAILY_BET_TOTAL:
            return ACResult(False, f"Дневной лимит ставок: {MAX_DAILY_BET_TOTAL}")
        return ACResult(True)

    def register_bet(self, chat_id: int, user_id: int, bet: int) -> None:
        from datetime import date
        day = date.today().isoformat()
        self._day_bets[(chat_id, user_id, day)] += bet

    def check_text(self, text: str) -> ACResult:
        if len(text) > MAX_TEXT_CMD_LEN:
            return ACResult(False, "Слишком длинная команда")
        # block obvious injection noise
        bad = ("\x00", "<script", "javascript:", "${", "{{")
        low = text.lower()
        for b in bad:
            if b in low:
                return ACResult(False, "Подозрительный ввод")
        return ACResult(True)

    def suspicion(self, user_id: int) -> int:
        return int(self._flags.get(user_id, 0))


anticheat = AntiCheatEngine()
