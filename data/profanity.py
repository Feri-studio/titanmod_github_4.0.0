"""Default profanity / spam token packs used by automod.

These are coarse token lists for substring matching. Chats can extend them
with /addbadword. Keep lists conservative: no sexual content, just common
abuse, scam and spam markers.
"""

from __future__ import annotations

ABUSE_RU = [
    "дурак", "идиот", "кретин", "тупой", "дебил", "мудак", "сволочь",
    "подонок", "мразь", "гад", "скотина", "урод", "лох", "чмо", "гнида",
    "падла", "тварь", "баран", "олух", "болван", "недоумок", "тупица",
    "придурок", "отморозок", "выродок", "шавка", "крыса", "шакал",
]

ABUSE_EN = [
    "idiot", "stupid", "dumbass", "moron", "loser", "jerk", "trash",
    "noob", "retard", "scum", "clown", "garbage", "worthless",
]

SCAM_MARKERS = [
    "free nitro", "steam gift", "airdrop", "double your", "crypto giveaway",
    "wallet connect", "seed phrase", "private key", "metamask", "без вложений",
    "гарант накрут", "накрутка подписчиков", "заработок без", "инвест клуб",
    "пирамида", "хайп проект", "раздача nft", "чек на 1000", "вывод прибыли",
    "binance support", "telegram premium free", "взлом вк", "взлом инсты",
    "купить голоса", "продам акк", "слив базы", "базы номеров",
]

INVITE_SPAM = [
    "t.me/joinchat", "t.me/+", "telegram.me/joinchat", "bit.ly/", "cutt.ly/",
    "tinyurl.com", "clck.ru", "goo.su", "shorturl",
]

CASINO_SPAM = [
    "казино", "слоты", "ставки на спорт", "букмекер", "промокод казино",
    "бездепозит", "фриспины", "1xbet", "melbet", "pin-up", "pokerdom",
]

ADS_RU = [
    "переходи в бот", "пиши в лс", "куплю рекламу", "продам рекламу",
    "взаимная подписка", "взаимные лайки", "накрутка", "накручу",
    "прайс на рекламу", "размещение в каналах", "сео продвижение",
]

PHONE_SCAM = [
    "перевод на карту", "код из смс", "скажи код", "подтверди код",
    "cvv карты", "срок карты", "3ds пароль",
]


def default_bad_tokens() -> list[str]:
    seen = set()
    out = []
    for pack in (ABUSE_RU, ABUSE_EN, SCAM_MARKERS, INVITE_SPAM, CASINO_SPAM, ADS_RU, PHONE_SCAM):
        for w in pack:
            key = w.lower().strip()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
    return out


def token_hits(text: str) -> list[str]:
    t = (text or "").lower()
    if not t:
        return []
    return [w for w in default_bad_tokens() if w in t]


CATEGORY_PACKS = {
    "abuse": ABUSE_RU + ABUSE_EN,
    "scam": SCAM_MARKERS + PHONE_SCAM,
    "ads": ADS_RU + INVITE_SPAM,
    "casino": CASINO_SPAM,
}


def hits_by_category(text: str) -> dict[str, list[str]]:
    t = (text or "").lower()
    result = {}
    for cat, words in CATEGORY_PACKS.items():
        found = [w for w in words if w in t]
        if found:
            result[cat] = found
    return result
