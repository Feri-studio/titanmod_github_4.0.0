"""
TitanMod Web Panel — expanded admin UI.

  uvicorn panel.main:app --host 127.0.0.1 --port 8080
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import config
from panel import auth, db_sync as db

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))

app = FastAPI(title="TitanMod Panel", docs_url=None, redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=(config.BOT_TOKEN or "titanmod-panel") + "-panel",
)
(ROOT / "static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


def ok_auth(request: Request) -> bool:
    return auth.valid_session(request.session.get(auth.SESSION_COOKIE))


def guard(request: Request):
    if not ok_auth(request):
        return RedirectResponse("/login", status_code=303)
    return None


def ctx(request: Request, page: str, **extra):
    base = {
        "request": request,
        "bot": config.BOT_NAME,
        "ver": config.VERSION,
        "page": page,
    }
    base.update(extra)
    return base


# ── auth ──────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if ok_auth(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", ctx(request, "", error=None))


@app.post("/login")
async def login_post(request: Request, password: str = Form(...)):
    if auth.check_password(password):
        request.session[auth.SESSION_COOKIE] = auth.make_session()
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        ctx(request, "", error="Неверный пароль"),
        status_code=401,
    )


@app.get("/logout")
async def logout(request: Request):
    auth.drop_session(request.session.get(auth.SESSION_COOKIE))
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ── pages ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "dashboard.html",
        ctx(request, "dashboard", stats=db.stats_overview(), chats=db.list_chats(25)),
    )


@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    if (r := guard(request)):
        return r
    chats = db.list_chats(500)
    for c in chats:
        c["_s"] = db.parse_settings(c.get("settings"))
    return templates.TemplateResponse("chats.html", ctx(request, "chats", chats=chats))


@app.get("/chats/{chat_id}", response_class=HTMLResponse)
async def chat_detail(request: Request, chat_id: int):
    if (r := guard(request)):
        return r
    chat = db.get_chat(chat_id)
    if not chat:
        return PlainTextResponse("Chat not found", status_code=404)
    settings = db.parse_settings(chat.get("settings"))
    return templates.TemplateResponse(
        "chat_detail.html",
        ctx(
            request,
            "chats",
            chat=chat,
            settings=settings,
            settings_json=json.dumps(settings, ensure_ascii=False, indent=2),
            warns=db.list_warns(chat_id, limit=40),
            notes=db.list_notes(chat_id, 40),
            filters=db.list_filters(chat_id, 40),
            ranks=db.list_ranks(chat_id, 40),
            saved=request.query_params.get("saved"),
        ),
    )


@app.post("/chats/{chat_id}/settings")
async def chat_settings_save(request: Request, chat_id: int, settings_json: str = Form(...)):
    if (r := guard(request)):
        return r
    try:
        data = json.loads(settings_json)
        if not isinstance(data, dict):
            raise ValueError("need object")
    except Exception:
        return PlainTextResponse("Invalid JSON", status_code=400)
    if not db.get_chat(chat_id):
        return PlainTextResponse("Not found", status_code=404)
    db.save_settings(chat_id, data)
    return RedirectResponse(f"/chats/{chat_id}?saved=1", status_code=303)


@app.post("/chats/{chat_id}/activate")
async def chat_activate(request: Request, chat_id: int, activated: int = Form(1)):
    if (r := guard(request)):
        return r
    db.patch_setting(chat_id, "group_activated", 1 if int(activated) else 0)
    return RedirectResponse(f"/chats/{chat_id}", status_code=303)


@app.post("/chats/{chat_id}/toggle")
async def chat_toggle(request: Request, chat_id: int, key: str = Form(...), value: int = Form(0)):
    if (r := guard(request)):
        return r
    allowed = {
        "welcome_enabled", "welcome_captcha", "antiflood", "antispam", "raid_mode",
        "nightmode", "force_sub", "reports", "filters_enabled", "group_activated",
    }
    if key not in allowed:
        return PlainTextResponse("key not allowed", status_code=400)
    db.patch_setting(chat_id, key, int(value))
    return RedirectResponse(f"/chats/{chat_id}", status_code=303)


@app.get("/warns", response_class=HTMLResponse)
async def warns_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "warns",
            title="Варны",
            rows=db.list_warns(limit=300),
            columns=["id", "chat_id", "user_id", "admin_id", "reason", "created_at"],
            actions_warn_delete=True,
        ),
    )


@app.post("/warns/{warn_id}/delete")
async def warn_delete(request: Request, warn_id: int):
    if (r := guard(request)):
        return r
    db.delete_warn(warn_id)
    return RedirectResponse("/warns", status_code=303)


@app.get("/punishments", response_class=HTMLResponse)
async def punishments_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "punishments",
            title="Наказания",
            rows=db.list_punishments(limit=300),
            columns=["id", "chat_id", "user_id", "admin_id", "type", "reason", "created_at"],
        ),
    )


@app.get("/gbans", response_class=HTMLResponse)
async def gbans_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "gbans.html",
        ctx(request, "gbans", rows=db.list_gbans(300)),
    )


@app.post("/gbans/add")
async def gban_add(request: Request, user_id: int = Form(...), reason: str = Form("panel")):
    if (r := guard(request)):
        return r
    db.set_gban(user_id, reason)
    return RedirectResponse("/gbans", status_code=303)


@app.post("/gbans/{user_id}/remove")
async def gban_remove(request: Request, user_id: int):
    if (r := guard(request)):
        return r
    db.un_gban(user_id)
    return RedirectResponse("/gbans", status_code=303)


@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_tickets(150)
    cols = list(rows[0].keys()) if rows else ["id", "status"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "tickets", title="Тикеты", rows=rows, columns=cols),
    )


@app.get("/economy", response_class=HTMLResponse)
async def economy_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "economy.html",
        ctx(request, "economy", rows=db.list_economy_top(80)),
    )


@app.post("/economy/set")
async def economy_set(
    request: Request,
    chat_id: int = Form(...),
    user_id: int = Form(...),
    balance: int = Form(...),
):
    if (r := guard(request)):
        return r
    db.set_balance(chat_id, user_id, balance)
    return RedirectResponse("/economy", status_code=303)


@app.get("/notes", response_class=HTMLResponse)
async def notes_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_notes(limit=200)
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "notes",
            title="Заметки",
            rows=rows,
            columns=["id", "chat_id", "name", "content", "admin_id", "created_at"],
        ),
    )


@app.get("/filters", response_class=HTMLResponse)
async def filters_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_filters(limit=200)
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "filters",
            title="Фильтры",
            rows=rows,
            columns=["id", "chat_id", "keyword", "content", "uses", "created_at"],
        ),
    )


@app.get("/badwords", response_class=HTMLResponse)
async def badwords_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "badwords",
            title="Чёрный список слов",
            rows=db.list_badwords(limit=400),
            columns=["id", "chat_id", "word"],
        ),
    )


@app.get("/ranks", response_class=HTMLResponse)
async def ranks_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "ranks",
            title="Ранги штата",
            rows=db.list_ranks(limit=300),
            columns=["chat_id", "user_id", "level", "title", "set_by", "updated_at"],
        ),
    )


@app.get("/feds", response_class=HTMLResponse)
async def feds_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "feds.html",
        ctx(
            request,
            "feds",
            feds=db.list_federations(100),
            bans=db.list_fed_bans(150),
        ),
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_reports(150)
    cols = list(rows[0].keys()) if rows else ["id"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "reports", title="Репорты", rows=rows, columns=cols),
    )


@app.get("/modstats", response_class=HTMLResponse)
async def modstats_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "modstats",
            title="Стата модераторов",
            rows=db.list_mod_stats(150),
            columns=["chat_id", "admin_id", "action", "cnt"],
        ),
    )


@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_event_log(200)
    cols = list(rows[0].keys()) if rows else ["id"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "events", title="Event log", rows=rows, columns=cols),
    )


@app.get("/xp", response_class=HTMLResponse)
async def xp_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "xp",
            title="XP / уровни",
            rows=db.list_xp_top(80),
            columns=["chat_id", "user_id", "xp", "level", "messages"],
        ),
    )


@app.get("/rep", response_class=HTMLResponse)
async def rep_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "rep",
            title="Репутация",
            rows=db.list_rep_top(80),
            columns=["chat_id", "user_id", "score"],
        ),
    )


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_inventory(150)
    cols = list(rows[0].keys()) if rows else ["chat_id", "user_id", "item"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "inventory", title="Инвентарь", rows=rows, columns=cols),
    )


@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_scheduled(50)
    cols = list(rows[0].keys()) if rows else ["id", "chat_id", "run_at"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "schedule", title="Отложенные посты", rows=rows, columns=cols),
    )


@app.get("/marriages", response_class=HTMLResponse)
async def marriages_page(request: Request):
    if (r := guard(request)):
        return r
    return templates.TemplateResponse(
        "table.html",
        ctx(
            request,
            "marriages",
            title="Браки",
            rows=db.list_marriages(80),
            columns=["chat_id", "user_a", "user_b", "since"],
        ),
    )


@app.get("/disabled", response_class=HTMLResponse)
async def disabled_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_disabled(200)
    cols = list(rows[0].keys()) if rows else ["chat_id", "command"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "disabled", title="Выключенные команды", rows=rows, columns=cols),
    )


@app.get("/approved", response_class=HTMLResponse)
async def approved_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_approved(200)
    cols = list(rows[0].keys()) if rows else ["chat_id", "user_id"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "approved", title="Approved", rows=rows, columns=cols),
    )


@app.get("/quarantine", response_class=HTMLResponse)
async def quarantine_page(request: Request):
    if (r := guard(request)):
        return r
    rows = db.list_quarantine(100)
    cols = list(rows[0].keys()) if rows else ["chat_id", "user_id"]
    return templates.TemplateResponse(
        "table.html",
        ctx(request, "quarantine", title="Карантин", rows=rows, columns=cols),
    )


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = ""):
    if (r := guard(request)):
        return r
    users = db.search_user(q) if q else []
    warns = []
    if q and q.lstrip("-").isdigit():
        warns = db.list_warns(user_id=int(q), limit=30)
    return templates.TemplateResponse(
        "search.html",
        ctx(request, "search", q=q, users=users, warns=warns),
    )


@app.get("/settings", response_class=HTMLResponse)
async def global_settings(request: Request):
    if (r := guard(request)):
        return r
    info = {
        "BOT_NAME": config.BOT_NAME,
        "VERSION": config.VERSION,
        "DB_PATH": config.DB_PATH,
        "ADMINS": config.ADMINS,
        "DEFAULT_LANG": config.DEFAULT_LANG,
        "CAPTCHA_TTL": config.CAPTCHA_TTL,
        "RAID_JOINS": config.RAID_JOINS,
        "RAID_WINDOW": config.RAID_WINDOW,
        "SCHEDULER_TICK": config.SCHEDULER_TICK,
        "ACTIVATE_CODE_configured": bool(config.ACTIVATE_CODE),
        "tables": ", ".join(db.list_tables()[:40]),
    }
    return templates.TemplateResponse("settings.html", ctx(request, "settings", info=info))


@app.get("/backup")
async def backup_download(request: Request):
    if (r := guard(request)):
        return r
    path = Path(config.DB_PATH)
    if not path.exists():
        return PlainTextResponse("DB not found", status_code=404)
    return FileResponse(
        path,
        filename=f"titanmod-{config.VERSION}.db",
        media_type="application/octet-stream",
    )


@app.get("/health")
async def health():
    return {"ok": True, "bot": config.BOT_NAME, "version": config.VERSION, "tables": len(db.list_tables())}
