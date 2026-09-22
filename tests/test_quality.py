"""Quality tests for TitanMod 4.3 — ranks, settings, tickets, economy."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_DB = Path("/tmp/titanmod_pytest.db")


def setup_module():
    if TEST_DB.exists():
        TEST_DB.unlink()
    os.environ["DB_PATH"] = str(TEST_DB)
    os.environ.setdefault("BOT_TOKEN", "0:test")
    os.environ.setdefault("BOT_ADMINS", "1")


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module", autouse=True)
def db_ready():
    setup_module()
    import config
    config.config.DB_PATH = str(TEST_DB)
    import database.db as db
    import database.extra as ex
    db.DB_PATH = db._resolve_db_path()
    ex.DB_PATH = db.DB_PATH
    run(db.init_db())
    yield
    try:
        TEST_DB.unlink(missing_ok=True)
    except Exception:
        pass


def test_version_file():
    v = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert v.startswith("4.")


def test_settings_persist():
    import database.db as db
    async def go():
        await db.update_settings(-1001, rules="Rule Z", welcome_enabled=1)
        s = await db.get_settings(-1001)
        assert s["rules"] == "Rule Z"
        assert s.get("welcome_enabled") in (1, True)
    run(go())


def test_ranks():
    import database.extra as ex
    async def go():
        await ex.set_user_rank(-1001, 42, 3, set_by=1)
        assert await ex.get_user_rank(-1001, 42) == 3
        await ex.set_user_rank(-1001, 42, 5, set_by=1)
        assert await ex.get_user_rank(-1001, 42) == 5
    run(go())


def test_economy_and_cooldown():
    import database.extra as ex
    async def go():
        bal = await ex.add_coins(-1001, 7, 100)
        assert bal >= 100
        ok, left = await ex.check_cooldown(-1001, 7, "work", 300)
        assert ok is True
        await ex.set_cooldown(-1001, 7, "work")
        ok2, left2 = await ex.check_cooldown(-1001, 7, "work", 300)
        assert ok2 is False
        assert left2 > 0
    run(go())


def test_tickets():
    import database.extra as ex
    async def go():
        tid = await ex.create_ticket(99, "help", -1001, "body")
        t = await ex.get_ticket(tid)
        assert t and t["status"] == "open"
        await ex.add_ticket_message(tid, 1, "staff reply")
        msgs = await ex.list_ticket_messages(tid)
        assert len(msgs) >= 2
        await ex.close_ticket(tid, 1)
        assert (await ex.get_ticket(tid))["status"] == "closed"
    run(go())


def test_catalog_no_empty():
    from core.commands import COMMANDS, ALL_COMMAND_NAMES
    assert len(COMMANDS) > 50
    assert len(ALL_COMMAND_NAMES) == len({c for c, _, _ in COMMANDS})


def test_rank_info_helpers():
    from core.ranks import get_rank_info, COMMAND_PERMS
    assert get_rank_info(7).has("ban")
    assert get_rank_info(0).has("ban") is False
    assert "ban" in COMMAND_PERMS


def test_bot_py_not_bloated():
    size = (ROOT / "bot.py").stat().st_size
    assert size < 100_000, f"bot.py too large: {size}"


def test_inventory_and_rep():
    import database.extra as ex
    async def go():
        await ex.inv_add(-2002, 5, "shield", 1, 0)
        assert await ex.inv_has(-2002, 5, "shield")
        ok, msg, score = await ex.rep_vote(-2002, 1, 5, 1)
        assert ok
        assert await ex.rep_get(-2002, 5) == score
    run(go())


def test_version_45():
    v = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert v == "4.5.0"
