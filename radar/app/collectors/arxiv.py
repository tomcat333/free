from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from app.collectors import RawItem

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML", "cs.NE", "cs.RO"]
ENDPOINT = "https://export.arxiv.org/api/query"


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return " ".join(el.text.split())


def parse_arxiv_feed(xml_text: str, source: str = "arxiv") -> list[RawItem]:
    root = ET.fromstring(xml_text)
    items: list[RawItem] = []
    for entry in root.findall(f"{ATOM}entry"):
        arxiv_id = _text(entry.find(f"{ATOM}id")).rstrip("/").split("/")[-1]
        title = _text(entry.find(f"{ATOM}title"))
        summary = _text(entry.find(f"{ATOM}summary"))
        published_raw = _text(entry.find(f"{ATOM}published"))
        published = None
        if published_raw:
            published = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
        authors = [_text(a.find(f"{ATOM}name")) for a in entry.findall(f"{ATOM}author")]
        pdf = ""
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"
        for link in entry.findall(f"{ATOM}link"):
            href = link.attrib.get("href", "")
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf = href
            if link.attrib.get("rel") == "alternate":
                abs_url = href or abs_url
        cats = [c.attrib.get("term", "") for c in entry.findall(f"{ATOM}category")]
        comment = _text(entry.find(f"{ARXIV_NS}comment"))
        items.append(
            RawItem(
                source=source,
                source_id=arxiv_id,
                url=abs_url,
                title=title,
                kind="paper",
                raw_summary=summary,
                authors=[a for a in authors if a],
                published_at=published,
                extra={"categories": cats, "comment": comment, "pdf": pdf},
                source_urls=[
                    {"label": "arXiv", "url": abs_url},
                    *([{"label": "PDF", "url": pdf}] if pdf else []),
                ],
            )
        )
    return items


async def collect_arxiv(client: httpx.AsyncClient) -> list[RawItem]:
    query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": "60",
    }
    resp = await client.get(ENDPOINT, params=params, headers={"Accept": "application/atom+xml"})
    resp.raise_for_status()
    return parse_arxiv_feed(resp.text)
