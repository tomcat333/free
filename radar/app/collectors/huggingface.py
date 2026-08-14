from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.collectors import RawItem

DAILY_PAPERS = "https://huggingface.co/api/daily_papers"
MODELS = "https://huggingface.co/api/models"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def parse_daily_papers(payload) -> list[RawItem]:
    items: list[RawItem] = []
    rows = payload if isinstance(payload, list) else payload.get("papers") or payload.get("items") or []
    for row in rows:
        paper = row.get("paper") if isinstance(row, dict) else None
        if not isinstance(paper, dict):
            paper = row if isinstance(row, dict) else {}
        arxiv_id = str(paper.get("id") or row.get("id") or "")
        title = (paper.get("title") or row.get("title") or "").strip()
        if not arxiv_id or not title:
            continue
        summary = paper.get("summary") or paper.get("abstract") or ""
        authors = []
        for a in paper.get("authors") or []:
            if isinstance(a, dict):
                authors.append(a.get("name") or a.get("user") or "")
            else:
                authors.append(str(a))
        upvotes = row.get("numComments") or paper.get("upvotes") or row.get("upvotes") or 0
        published = _parse_dt(row.get("publishedAt") or paper.get("publishedAt"))
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"
        hf_url = f"https://huggingface.co/papers/{arxiv_id}"
        items.append(
            RawItem(
                source="huggingface",
                source_id=f"paper:{arxiv_id}",
                url=hf_url,
                title=title,
                kind="paper",
                raw_summary=summary[:4000],
                authors=[a for a in authors if a],
                published_at=published,
                extra={"upvotes": upvotes, "arxiv_id": arxiv_id},
                source_urls=[
                    {"label": "Hugging Face Papers", "url": hf_url},
                    {"label": "arXiv", "url": abs_url},
                ],
            )
        )
    return items


def parse_models(payload) -> list[RawItem]:
    rows = payload if isinstance(payload, list) else payload.get("models") or []
    items: list[RawItem] = []
    for row in rows:
        model_id = row.get("id") or row.get("modelId") or ""
        if not model_id:
            continue
        url = f"https://huggingface.co/{model_id}"
        likes = row.get("likes") or 0
        downloads = row.get("downloads") or 0
        trending = row.get("trendingScore") or 0
        items.append(
            RawItem(
                source="huggingface",
                source_id=f"model:{model_id}",
                url=url,
                title=model_id,
                kind="model",
                raw_summary=(row.get("pipeline_tag") or "") + " " + " ".join(row.get("tags") or [])[:400],
                authors=[str(model_id).split("/")[0]],
                published_at=_parse_dt(row.get("createdAt") or row.get("lastModified")),
                extra={
                    "likes": likes,
                    "downloads": downloads,
                    "trendingScore": trending,
                    "pipeline_tag": row.get("pipeline_tag") or "",
                    "tags": row.get("tags") or [],
                },
                source_urls=[{"label": "Hugging Face", "url": url}],
            )
        )
    return items


async def collect_huggingface(client: httpx.AsyncClient) -> list[RawItem]:
    out: list[RawItem] = []
    papers = await client.get(DAILY_PAPERS)
    papers.raise_for_status()
    out.extend(parse_daily_papers(papers.json()))
    models = await client.get(MODELS, params={"sort": "trendingScore", "direction": "-1", "limit": "25"})
    models.raise_for_status()
    out.extend(parse_models(models.json()))
    return out
