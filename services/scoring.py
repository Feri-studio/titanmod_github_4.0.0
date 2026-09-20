"""Heuristic spam scoring for automod."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.text import (
    caps_ratio, emoji_count, extract_urls, has_invite, zalgo_count, has_rtl,
)
from data.profanity import hits_by_category, token_hits


URL_RE = re.compile(r"(https?://|t\.me/|www\.)", re.I)
REPEAT_CHAR = re.compile(r"(.)\1{6,}")
REPEAT_WORD = re.compile(r"(\b\w{2,}\b)(?:\s+\1){4,}", re.I)


@dataclass
class ScoreResult:
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    categories: dict = field(default_factory=dict)

    def add(self, points: int, reason: str):
        if points:
            self.score += points
            self.reasons.append(f"{reason}(+{points})")


def score_text(text: str, settings: dict | None = None) -> ScoreResult:
    s = settings or {}
    res = ScoreResult()
    raw = text or ""
    if not raw.strip():
        return res

    urls = extract_urls(raw)
    if urls:
        res.add(min(25, 8 * len(urls)), "urls")
    if has_invite(raw):
        res.add(35, "invite")
    if URL_RE.search(raw) and len(raw) < 40:
        res.add(15, "short-link-only")

    caps = caps_ratio(raw)
    if len(raw) >= int(s.get("caps_min", 8) or 8) and caps >= float(s.get("caps_percent", 70) or 70):
        res.add(18, "caps")

    em = emoji_count(raw)
    if em >= 12:
        res.add(12, "emoji-flood")
    elif em >= 6:
        res.add(6, "emoji")

    z = zalgo_count(raw)
    if z >= 8:
        res.add(20, "zalgo")
    if has_rtl(raw):
        res.add(10, "rtl")
    if REPEAT_CHAR.search(raw):
        res.add(10, "char-repeat")
    if REPEAT_WORD.search(raw):
        res.add(14, "word-repeat")

    hits = token_hits(raw)
    if hits:
        res.add(min(40, 8 * len(hits)), "bad-tokens")
        res.categories = hits_by_category(raw)

    if raw.count("\n") >= 12:
        res.add(8, "newline-flood")
    if len(raw) > 1800:
        res.add(10, "huge")
    return res


def should_delete(result: ScoreResult, threshold: int = 40) -> bool:
    return result.score >= threshold


def should_punish(result: ScoreResult, threshold: int = 70) -> bool:
    return result.score >= threshold


def describe(result: ScoreResult) -> str:
    if not result.reasons:
        return "чисто"
    return f"{result.score}: " + ", ".join(result.reasons)
