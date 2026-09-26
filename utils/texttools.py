"""Text helpers used by fun/util and filters."""
from __future__ import annotations

import hashlib
import random
import re
import string

LAYOUT_RU = "ёйцукенгшщзхъфывапролджэячсмитьбю.ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"
LAYOUT_EN = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?"


def switch_layout(text: str) -> str:
    table = str.maketrans(LAYOUT_RU + LAYOUT_EN, LAYOUT_EN + LAYOUT_RU)
    return (text or "").translate(table)


def mock_case(text: str) -> str:
    return "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text or ""))


def vaporwave(text: str) -> str:
    out = []
    for ch in text or "":
        o = ord(ch)
        if 33 <= o <= 126:
            out.append(chr(o + 0xFEE0))
        elif ch == " ":
            out.append("　")
        else:
            out.append(ch)
    return "".join(out)


def clap(text: str) -> str:
    parts = (text or "").split()
    return " 👏 ".join(parts) if parts else "👏"


def reverse_text(text: str) -> str:
    return (text or "")[::-1]


def gen_password(n: int = 16) -> str:
    n = max(6, min(n, 64))
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(alphabet) for _ in range(n))


def digest(text: str, algo: str = "sha256") -> str:
    data = (text or "").encode("utf-8")
    if algo == "md5":
        return hashlib.md5(data).hexdigest()
    if algo == "sha1":
        return hashlib.sha1(data).hexdigest()
    return hashlib.sha256(data).hexdigest()


SAFE_CALC = re.compile(r"^[0-9+\-*/().\s%]+$")


def safe_calc(expr: str) -> str:
    e = (expr or "").strip()
    if not e or not SAFE_CALC.match(e) or "**" in e:
        return "Можно только цифры и + - * / ( )"
    try:
        import ast
        import operator as op
        ops = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv, ast.Mod: op.mod, ast.USub: op.neg, ast.UAdd: op.pos,
        }
        def _ev(node):
            if isinstance(node, ast.Expression):
                return _ev(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Num):  # py<3.8
                return node.n
            if isinstance(node, ast.BinOp) and type(node.op) in ops:
                return ops[type(node.op)](_ev(node.left), _ev(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
                return ops[type(node.op)](_ev(node.operand))
            raise ValueError("bad")
        val = _ev(ast.parse(e, mode="eval"))
        return str(val)
    except Exception:
        return "Не посчиталось"


def choose(args: str) -> str:
    parts = re.split(r"\s+или\s+|,|;|\s+or\s+", args or "", flags=re.I)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        return "Дай варианты через запятую или «или»."
    return random.choice(parts)


EIGHTBALL = [
    "Да.", "Нет.", "Возможно.", "Спроси позже.", "Точно да.", "Точно нет.",
    "Шансы есть.", "Сомневаюсь.", "Звёзды говорят да.", "Лучше не надо.",
]


def eightball() -> str:
    return random.choice(EIGHTBALL)
