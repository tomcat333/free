from __future__ import annotations

from datetime import datetime, timezone

import feedparser
import httpx

from app.collectors import RawItem

FEEDS = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("Google AI", "https://blog.google/technology/ai/rss/"),
    ("DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("Meta AI", "https://ai.meta.com/blog/rss/"),
    ("NVIDIA Dev", "https://developer.nvidia.com/blog/feed/"),
    ("Microsoft AI", "https://blogs.microsoft.com/ai/feed/"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("Import AI", "https://importai.substack.com/feed"),
    ("MIT CSAIL", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
]


def parse_feed(xml_text: str, lab: str) -> list[RawItem]:
    parsed = feedparser.parse(xml_text)
    items: list[RawItem] = []
    for entry in parsed.entries[:20]:
        url = (entry.get("link") or "").strip()
        title = (entry.get("title") or "").strip()
        if not url or not title:
            continue
        summary = entry.get("summary") or entry.get("description") or ""
        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)
        elif entry.get("updated_parsed"):
            published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)
        items.append(
            RawItem(
                source="blog",
                source_id=entry.get("id") or url,
                url=url,
                title=f"[{lab}] {title}",
                kind="news",
                raw_summary=_strip_html(summary)[:3000],
                authors=[lab],
                published_at=published,
                extra={"lab": lab},
                source_urls=[{"label": lab, "url": url}],
            )
        )
    return items


def _strip_html(text: str) -> str:
    out = []
    skip = False
    for ch in text:
        if ch == "<":
            skip = True
            continue
        if ch == ">":
            skip = False
            out.append(" ")
            continue
        if not skip:
            out.append(ch)
    return " ".join("".join(out).split())


async def collect_blogs(client: httpx.AsyncClient) -> list[RawItem]:
    out: list[RawItem] = []
    for lab, url in FEEDS:
        try:
            resp = await client.get(url, headers={"Accept": "application/rss+xml, application/xml, text/xml"})
            if resp.status_code >= 400:
                continue
            out.extend(parse_feed(resp.text, lab))
        except httpx.HTTPError:
            continue
    return out
