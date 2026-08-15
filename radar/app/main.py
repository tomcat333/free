from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session, init_db
from app.dispatch import build_run_pack, dispatch_item
from app.models import CollectorRun, Dispatch, Item
from app.pipeline.briefing import TIER_LABEL, briefing_groups, load_feed, recent_window
from app.pipeline.enrich import ensure_deep_dive, ensure_intro

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["tier_label"] = lambda v: TIER_LABEL.get(v, v)
templates.env.filters["kind_label"] = lambda v: {
    "paper": "论文",
    "repo": "仓库",
    "model": "模型",
    "news": "实验室/博客",
    "discussion": "讨论",
}.get(v, v)


def db_dep():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    worker_task = None
    if settings.embed_worker:
        from app.worker import worker_loop

        worker_task = asyncio.create_task(worker_loop())
    yield
    if worker_task:
        worker_task.cancel()


app = FastAPI(title="前沿雷达", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    kind: str | None = None,
    q: str | None = None,
    session: Session = Depends(db_dep),
):
    items = load_feed(session, kind=kind or None, q=q, limit=80)
    if not q and not kind:
        window = recent_window(session, hours=48)
        groups = briefing_groups(window if window else items[:40])
    else:
        groups = briefing_groups(items)
    last_run = session.query(CollectorRun).order_by(CollectorRun.id.desc()).first()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "items": items,
            "groups": groups,
            "kind": kind or "",
            "q": q or "",
            "last_run": last_run,
            "llm_enabled": settings.llm_enabled,
            "llm_model": settings.openai_model if settings.llm_enabled else "",
            "env_file_found": settings.env_file_found,
            "dispatch_ready": bool(settings.dispatch_webhook_url),
            "total": session.query(Item).count(),
        },
    )


@app.get("/items/{item_id}", response_class=HTMLResponse)
def item_page(request: Request, item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    sources = _json_list(item.sources_json)
    extra = _json_obj(item.extra_json)
    dispatches = (
        session.query(Dispatch).filter(Dispatch.item_id == item.id).order_by(Dispatch.id.desc()).limit(5).all()
    )
    return templates.TemplateResponse(
        request=request,
        name="item.html",
        context={
            "item": item,
            "sources": sources,
            "extra": extra,
            "dispatches": dispatches,
            "llm_enabled": settings.llm_enabled,
            "llm_model": settings.openai_model if settings.llm_enabled else "",
            "env_file_found": settings.env_file_found,
            "dispatch_ready": bool(settings.dispatch_webhook_url),
        },
    )


@app.get("/api/status")
def api_status(session: Session = Depends(db_dep)):
    last_run = session.query(CollectorRun).order_by(CollectorRun.id.desc()).first()
    return {
        "total_items": session.query(Item).count(),
        "llm_enabled": settings.llm_enabled,
        "llm_model": settings.openai_model if settings.llm_enabled else "",
        "openai_base_url": settings.openai_base_url if settings.llm_enabled else "",
        "env_file_found": settings.env_file_found,
        "enrich_top_n": settings.enrich_top_n,
        "dispatch_ready": bool(settings.dispatch_webhook_url),
        "last_run": None
        if not last_run
        else {
            "status": last_run.status,
            "new_items": last_run.new_items,
            "started_at": last_run.started_at.isoformat() if last_run.started_at else None,
            "finished_at": last_run.finished_at.isoformat() if last_run.finished_at else None,
            "error": last_run.error,
            "detail": _json_obj(last_run.detail_json),
        },
    }


@app.get("/api/items")
def api_items(
    kind: str | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    session: Session = Depends(db_dep),
):
    items = load_feed(session, kind=kind, q=q, limit=limit)
    return [_item_dict(i) for i in items]


@app.get("/api/items/{item_id}")
def api_item(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    return _item_dict(item, full=True)


@app.post("/api/items/{item_id}/intro")
async def api_intro(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    item = await ensure_intro(session, item, force=True)
    return {"id": item.id, "brief": item.brief, "intro": item.intro}


@app.post("/api/items/{item_id}/deep-dive")
async def api_deep_dive(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    item = await ensure_deep_dive(session, item)
    return {"id": item.id, "deep_dive": item.deep_dive, "intro": item.intro, "brief": item.brief}


@app.post("/api/items/{item_id}/dispatch")
async def api_dispatch(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    row = await dispatch_item(session, item)
    return {
        "id": row.id,
        "status": row.status,
        "pack": json.loads(row.pack_json),
        "response_text": row.response_text,
    }


@app.get("/api/items/{item_id}/run-pack")
def api_run_pack(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    return build_run_pack(item)


@app.post("/collect")
async def trigger_collect(request: Request):
    from app.worker import collect_cycle

    result = await collect_cycle()
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse("/", status_code=303)
    return result


@app.post("/items/{item_id}/intro")
async def form_intro(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    await ensure_intro(session, item, force=True)
    return RedirectResponse(f"/items/{item_id}#intro", status_code=303)


@app.post("/items/{item_id}/deep-dive")
async def form_deep_dive(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    await ensure_deep_dive(session, item)
    return RedirectResponse(f"/items/{item_id}#deep", status_code=303)


@app.post("/items/{item_id}/dispatch")
async def form_dispatch(item_id: int, session: Session = Depends(db_dep)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "条目不存在")
    await dispatch_item(session, item)
    return RedirectResponse(f"/items/{item_id}#run", status_code=303)


def _item_dict(item: Item, full: bool = False) -> dict:
    data = {
        "id": item.id,
        "title": item.title,
        "url": item.url,
        "kind": item.kind,
        "source": item.source,
        "score": item.score,
        "tier": item.tier,
        "brief": item.brief,
        "tags": [t for t in (item.tags or "").split(",") if t],
        "published_at": item.published_at.isoformat() if item.published_at else None,
    }
    if full:
        data.update(
            {
                "authors": item.authors,
                "raw_summary": item.raw_summary,
                "intro": item.intro,
                "deep_dive": item.deep_dive,
                "score_reasons": item.score_reasons,
                "sources": _json_list(item.sources_json),
                "extra": _json_obj(item.extra_json),
            }
        )
    return data


def _json_list(raw: str) -> list:
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _json_obj(raw: str) -> dict:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}
