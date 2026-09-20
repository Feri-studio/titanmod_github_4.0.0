from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def parse_buttons(text: str) -> tuple[str, str | None]:
    """
    Parse notes/filters button syntax:
    text && btn1=url && btn2=url && same
    Use 'same' to stay on row.
    """
    if not text:
        return "", None
    if "&&" not in text:
        return text, None
    parts = [p.strip() for p in text.split("&&")]
    body = parts[0]
    spec = "&&".join(parts[1:]).strip()
    return body, spec or None


def build_markup(spec: str | None) -> InlineKeyboardMarkup | None:
    if not spec:
        return None
    builder = InlineKeyboardBuilder()
    row = []
    tokens = [t.strip() for t in spec.split("&&") if t.strip()]
    for tok in tokens:
        if tok.lower() == "same":
            continue
        if "=" not in tok:
            continue
        label, url = tok.split("=", 1)
        label, url = label.strip(), url.strip()
        if not label or not url:
            continue
        row.append(InlineKeyboardButton(text=label, url=url))
        # new row unless next token is 'same' handled by grouping
    # rebuild with same-support
    builder = InlineKeyboardBuilder()
    current: list[InlineKeyboardButton] = []
    i = 0
    items = []
    for tok in tokens:
        if tok.lower() == "same":
            if items:
                items[-1]["same"] = True
            continue
        if "=" not in tok:
            continue
        label, url = tok.split("=", 1)
        items.append({"label": label.strip(), "url": url.strip(), "same": False})
    row = []
    for it in items:
        row.append(InlineKeyboardButton(text=it["label"], url=it["url"]))
        if not it["same"]:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    try:
        return builder.as_markup()
    except Exception:
        return None
