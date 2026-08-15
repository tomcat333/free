from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

import httpx

from app.collectors.arxiv import collect_arxiv
from app.collectors.blogs import collect_blogs
from app.collectors.github import collect_github
from app.collectors.hn import collect_hn
from app.collectors.huggingface import collect_huggingface
from app.collectors.pro_xray import collect_arxiv_pro, collect_vendors
from app.collectors.reddit import collect_reddit
from app.config import settings

log = logging.getLogger(__name__)

CollectorFn = Callable[[httpx.AsyncClient], Awaitable[list]]

COLLECTORS: dict[str, CollectorFn] = {
    "arxiv": collect_arxiv,
    "arxiv_pro": collect_arxiv_pro,
    "github": collect_github,
    "hn": collect_hn,
    "huggingface": collect_huggingface,
    "blogs": collect_blogs,
    "reddit": collect_reddit,
    "vendors": collect_vendors,
}


async def collect_all() -> dict[str, list]:
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    timeout = httpx.Timeout(30.0, connect=15.0)
    results: dict[str, list] = {}
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
        tasks = {name: asyncio.create_task(_run(name, fn, client)) for name, fn in COLLECTORS.items()}
        for name, task in tasks.items():
            results[name] = await task
    return results


async def _run(name: str, fn: CollectorFn, client: httpx.AsyncClient) -> list:
    try:
        items = await fn(client)
        log.info("collector %s fetched %s items", name, len(items))
        return items
    except Exception:
        log.exception("collector %s failed", name)
        return []
