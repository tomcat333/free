from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item

TIER_LABEL = {
    "breakthrough": "重点突破",
    "notable": "值得看",
    "signal": "雷达扫描",
}


def load_feed(session: Session, *, kind: str | None = None, q: str | None = None, limit: int = 80) -> list[Item]:
    stmt = select(Item).order_by(Item.score.desc(), Item.collected_at.desc())
    if kind:
        stmt = stmt.where(Item.kind == kind)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Item.title.ilike(like) | Item.raw_summary.ilike(like) | Item.brief.ilike(like))
    return list(session.scalars(stmt.limit(limit)))


def briefing_groups(items: list[Item]) -> dict[str, list[Item]]:
    groups = {"breakthrough": [], "notable": [], "signal": []}
    for item in items:
        groups.setdefault(item.tier, []).append(item)
    return groups


def recent_window(session: Session, hours: int = 36) -> list[Item]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    stmt = (
        select(Item)
        .where(Item.collected_at >= since)
        .order_by(Item.score.desc(), Item.collected_at.desc())
        .limit(120)
    )
    return list(session.scalars(stmt))
