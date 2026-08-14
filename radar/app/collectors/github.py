from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.collectors import RawItem
from app.config import settings

SEARCH_URL = "https://api.github.com/search/repositories"

QUERIES = [
    "llm OR transformer OR \"diffusion model\" created:>{since} stars:>8",
    "topic:machine-learning created:>{since} stars:>15",
    "topic:large-language-models created:>{since} stars:>5",
    "\"world model\" OR \"reasoning model\" created:>{since} stars:>5",
]


def parse_github_search(payload: dict) -> list[RawItem]:
    items: list[RawItem] = []
    for repo in payload.get("items") or []:
        full_name = repo.get("full_name") or ""
        html_url = repo.get("html_url") or ""
        if not full_name or not html_url:
            continue
        created = _parse_dt(repo.get("created_at"))
        pushed = _parse_dt(repo.get("pushed_at"))
        desc = (repo.get("description") or "").strip()
        items.append(
            RawItem(
                source="github",
                source_id=str(repo.get("id") or full_name),
                url=html_url,
                title=full_name,
                kind="repo",
                raw_summary=desc,
                authors=[repo.get("owner", {}).get("login") or ""],
                published_at=created or pushed,
                extra={
                    "stars": repo.get("stargazers_count") or 0,
                    "forks": repo.get("forks_count") or 0,
                    "language": repo.get("language") or "",
                    "topics": repo.get("topics") or [],
                    "clone_url": repo.get("clone_url") or html_url + ".git",
                    "default_branch": repo.get("default_branch") or "main",
                },
                source_urls=[{"label": "GitHub", "url": html_url}],
            )
        )
    return items


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)


async def collect_github(client: httpx.AsyncClient) -> list[RawItem]:
    since = (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    seen: set[str] = set()
    out: list[RawItem] = []
    for q in QUERIES:
        resp = await client.get(
            SEARCH_URL,
            params={"q": q.format(since=since), "sort": "stars", "order": "desc", "per_page": 20},
            headers=headers,
        )
        if resp.status_code == 403:
            break
        resp.raise_for_status()
        for item in parse_github_search(resp.json()):
            if item.url in seen:
                continue
            seen.add(item.url)
            out.append(item)
    return out
