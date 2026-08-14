from __future__ import annotations

from datetime import datetime, timezone

import feedparser
import httpx

from app.collectors import RawItem
from app.collectors.blogs import _strip_html

SUBREDDITS = ["MachineLearning", "LocalLLaMA", "LanguageTechnology", "singularity"]


def parse_reddit_listing(payload: dict, subreddit: str) -> list[RawItem]:
    items: list[RawItem] = []
    children = (payload.get("data") or {}).get("children") or []
    for child in children:
        data = child.get("data") or {}
        post_id = data.get("id") or ""
        title = (data.get("title") or "").strip()
        if not post_id or not title or data.get("stickied"):
            continue
        if _skip_title(title):
            continue
        permalink = data.get("permalink") or f"/r/{subreddit}/comments/{post_id}"
        url = "https://www.reddit.com" + permalink
        created = data.get("created_utc")
        published = datetime.fromtimestamp(created, tz=timezone.utc).replace(tzinfo=None) if created else None
        items.append(
            RawItem(
                source="reddit",
                source_id=post_id,
                url=url,
                title=title,
                kind="discussion",
                raw_summary=(data.get("selftext") or "")[:2500],
                authors=[data.get("author") or ""],
                published_at=published,
                extra={
                    "score": data.get("score") or 0,
                    "comments": data.get("num_comments") or 0,
                    "subreddit": subreddit,
                    "external_url": data.get("url") or "",
                    "flair": data.get("link_flair_text") or "",
                },
                source_urls=[
                    {"label": f"r/{subreddit}", "url": url},
                    *([{"label": "外链", "url": data["url"]}] if data.get("url") and data.get("url") != url else []),
                ],
            )
        )
    return items


def parse_reddit_rss(xml_text: str, subreddit: str) -> list[RawItem]:
    parsed = feedparser.parse(xml_text)
    items: list[RawItem] = []
    for entry in parsed.entries:
        title = (entry.get("title") or "").strip()
        url = (entry.get("link") or "").strip()
        if not title or not url or _skip_title(title):
            continue
        if (entry.get("author") or "").endswith("AutoModerator"):
            continue
        source_id = (entry.get("id") or url).split("/")[-1]
        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)
        items.append(
            RawItem(
                source="reddit",
                source_id=source_id,
                url=url,
                title=title,
                kind="discussion",
                raw_summary=_strip_html(entry.get("summary") or "")[:2500],
                authors=[entry.get("author") or ""],
                published_at=published,
                extra={"subreddit": subreddit, "via": "rss"},
                source_urls=[{"label": f"r/{subreddit}", "url": url}],
            )
        )
    return items


def _skip_title(title: str) -> bool:
    lowered = title.lower()
    return "self-promotion thread" in lowered or "daily discussion" in lowered


async def collect_reddit(client: httpx.AsyncClient) -> list[RawItem]:
    out: list[RawItem] = []
    for sub in SUBREDDITS:
        json_resp = await client.get(
            f"https://www.reddit.com/r/{sub}/hot.json",
            params={"limit": 20, "raw_json": 1},
            headers={"Accept": "application/json"},
        )
        if json_resp.status_code < 400:
            out.extend(parse_reddit_listing(json_resp.json(), sub))
            continue
        rss = await client.get(
            f"https://www.reddit.com/r/{sub}/hot/.rss",
            headers={"Accept": "application/atom+xml, application/rss+xml, text/xml"},
        )
        if rss.status_code >= 400:
            continue
        out.extend(parse_reddit_rss(rss.text, sub))
    return out
