from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.collectors import RawItem
from app.models import Item
from app.pipeline.score import score_item


def ingest_raw_items(session: Session, batches: dict[str, list[RawItem]]) -> list[Item]:
    created: list[Item] = []
    for _name, items in batches.items():
        for raw in items:
            if not raw.url or not raw.title:
                continue
            existing = session.query(Item).filter(Item.url == raw.url).one_or_none()
            score, reasons, tier = score_item(raw)
            if existing:
                existing.score = max(existing.score, score)
                existing.score_reasons = " | ".join(reasons)
                existing.tier = existing.tier if existing.score >= score else tier
                if raw.raw_summary and len(raw.raw_summary) > len(existing.raw_summary or ""):
                    existing.raw_summary = raw.raw_summary
                continue
            item = Item(
                source=raw.source,
                source_id=raw.source_id[:400],
                url=raw.url[:1000],
                title=raw.title[:500],
                kind=raw.kind,
                authors=", ".join(a for a in raw.authors if a)[:1000],
                raw_summary=raw.raw_summary,
                extra_json=json.dumps(raw.extra, ensure_ascii=False),
                published_at=raw.published_at,
                score=score,
                score_reasons=" | ".join(reasons),
                tier=tier,
                tags=_tags(raw),
                brief=_fallback_brief(raw),
                intro="",
                deep_dive="",
                sources_json=json.dumps(raw.source_urls, ensure_ascii=False),
                collected_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(item)
            created.append(item)
    session.commit()
    for item in created:
        session.refresh(item)
    return created


def _fallback_brief(raw: RawItem) -> str:
    text = (raw.raw_summary or "").strip()
    if not text:
        return f"{raw.kind} · 来自 {raw.source}"
    return text.split("\n")[0][:220]


def _tags(raw: RawItem) -> str:
    tags = {raw.kind, raw.source}
    extra = raw.extra or {}
    for topic in extra.get("topics") or []:
        tags.add(str(topic)[:40])
    if extra.get("pipeline_tag"):
        tags.add(str(extra["pipeline_tag"]))
    if extra.get("lab"):
        tags.add(str(extra["lab"]))
    return ",".join(sorted(tags)[:12])
