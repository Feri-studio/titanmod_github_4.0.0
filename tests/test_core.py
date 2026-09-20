import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.timeparse import parse_time, format_time, is_night, parse_hhmm
from core.text import caps_ratio, extract_urls, has_invite, mention_count, zalgo_count
from core.commands import COMMANDS, ALL_COMMAND_NAMES
from datetime import datetime
from services.locks import parse_lock_set, dump_lock_set


def test_parse_time():
    assert parse_time("10s") == 10
    assert parse_time("5m") == 300
    assert parse_time("2h") == 7200
    assert parse_time("1d") == 86400
    assert parse_time("1w") >= 604800
    assert parse_time("1h30m") == 5400
    assert parse_time("10") == 600  # minutes fallback


def test_format_time():
    assert "ч" in format_time(3600) or "мин" in format_time(60)
    assert format_time(0) == "навсегда"


def test_night():
    now = datetime(2026, 1, 1, 1, 0)
    assert is_night(now, "23:00", "07:00") is True
    now2 = datetime(2026, 1, 1, 12, 0)
    assert is_night(now2, "23:00", "07:00") is False
    assert parse_hhmm("23:00") == (23, 0)


def test_text_helpers():
    assert extract_urls("see https://example.com please")
    assert has_invite("join t.me/+abcdef")
    assert mention_count("hello @user_name") >= 1
    assert caps_ratio("AAAAAA") > 90
    assert zalgo_count("a") == 0


def test_locks_set():
    s = parse_lock_set("url,sticker,nope")
    assert "url" in s and "sticker" in s and "nope" not in s
    assert "url" in dump_lock_set(s)


def test_catalog():
    assert len(COMMANDS) > 80
    assert "ban" in ALL_COMMAND_NAMES
    assert "settings" in ALL_COMMAND_NAMES


if __name__ == "__main__":
    test_parse_time()
    test_format_time()
    test_night()
    test_text_helpers()
    test_locks_set()
    test_catalog()
    print("ok")
