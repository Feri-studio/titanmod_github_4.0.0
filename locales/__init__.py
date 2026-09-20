from .ru import RU
from .en import EN

LANGS = {"ru": RU, "en": EN}


def t(lang: str, key: str, **kwargs) -> str:
    table = LANGS.get(lang) or RU
    text = table.get(key) or RU.get(key) or key
    try:
        return text.format(**kwargs)
    except Exception:
        return text
