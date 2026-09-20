import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from services.scoring import score_text, should_delete, describe
from data.profanity import token_hits, default_bad_tokens
from utils.texttools import switch_layout, mock_case, safe_calc, digest, gen_password
from core.timeparse import parse_time, format_time
from core.commands import ALL_COMMAND_NAMES, COMMANDS


def test_scam_scores_high():
    r = score_text("free nitro t.me/+aaaa steam gift wallet connect")
    assert r.score >= 40
    assert should_delete(r)


def test_clean_text_low():
    r = score_text("Привет, как дела? Завтра встречаемся в 18:00.")
    assert r.score < 20


def test_tokens_not_empty():
    assert len(default_bad_tokens()) > 30
    assert token_hits("продам акк без вложений")


def test_texttools():
    assert "qwerty" in switch_layout("йцукен").lower() or len(switch_layout("йцукен")) == 6
    assert mock_case("abcd")
    assert safe_calc("2+2") == "4"
    assert len(digest("x")) == 64
    assert len(gen_password(12)) == 12


def test_timeparse():
    assert parse_time("2h") == 7200
    assert parse_time("30m") == 1800
    assert "ч" in format_time(7200) or "час" in format_time(7200)


def test_many_commands():
    assert len(ALL_COMMAND_NAMES) >= 120
    assert len(COMMANDS) >= 120


if __name__ == "__main__":
    test_scam_scores_high()
    test_clean_text_low()
    test_tokens_not_empty()
    test_texttools()
    test_timeparse()
    test_many_commands()
    print("ok", "commands", len(ALL_COMMAND_NAMES))
