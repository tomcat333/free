from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.collectors import RawItem

ENDPOINT = "https://hn.algolia.com/api/v1/search_by_date"
QUERIES = [
    "LLM OR GPT OR Claude OR Gemini OR \"open source model\"",
    "transformer OR diffusion OR \"world model\" OR SOTA",
    "\"machine learning\" OR \"deep learning\" algorithm",
]


def parse_hn(payload: dict) -> list[RawItem]:
    items: list[RawItem] = []
    for hit in payload.get("hits") or []:
        object_id = str(hit.get("objectID") or "")
        title = (hit.get("title") or "").strip()
        if not object_id or not title:
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        created = hit.get("created_at")
        published = None
        if created:
            published = datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        items.append(
            RawItem(
                source="hn",
                source_id=object_id,
                url=url,
                title=title,
                kind="discussion",
                raw_summary=(hit.get("story_text") or "")[:2000],
                authors=[hit.get("author") or ""],
                published_at=published,
                extra={"points": points, "comments": comments, "hn_id": object_id},
                source_urls=[
                    {"label": "原文", "url": url},
                    {"label": "HN 讨论", "url": f"https://news.ycombinator.com/item?id={object_id}"},
                ],
            )
        )
    return items


async def collect_hn(client: httpx.AsyncClient) -> list[RawItem]:
    seen: set[str] = set()
    out: list[RawItem] = []
    for q in QUERIES:
        resp = await client.get(
            ENDPOINT,
            params={"query": q, "tags": "story", "hitsPerPage": 25, "numericFilters": "points>8"},
        )
        resp.raise_for_status()
        for item in parse_hn(resp.json()):
            if item.source_id in seen:
                continue
            seen.add(item.source_id)
            out.append(item)
    return out
