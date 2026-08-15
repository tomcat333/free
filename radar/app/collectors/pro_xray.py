from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import feedparser
import httpx

from app.collectors import RawItem
from app.collectors.arxiv import ENDPOINT, parse_arxiv_feed

# 专业方向：CD-SAXS / SAXS 关键尺寸 / HRXRD / 半导体 X 射线表征
ARXIV_PRO_QUERY = (
    'all:"CD-SAXS" OR all:"CDSAXS" OR all:"critical-dimension SAXS" OR '
    'all:"critical dimension SAXS" OR (all:SAXS AND all:"critical dimension") OR '
    'all:HRXRD OR all:"high-resolution XRD" OR all:"high resolution X-ray diffraction" OR '
    '(all:GISAXS AND (all:semiconductor OR all:lithography OR all:nanopattern)) OR '
    '(all:XRD AND all:semiconductor AND (all:metrology OR all:epitaxy OR all:thin film)) OR '
    '(all:"X-ray reflectivity" AND all:semiconductor) OR '
    '(all:XRR AND all:semiconductor)'
)

RIGAKU_HOLDINGS_NEWS = "https://rigaku-holdings.com/english/news/"
RIGAKU_COM_NEWS = "https://rigaku.com/about/news-and-press-releases"
KLA_PRESS_RSS = "https://ir.kla.com/news-events/press-releases/rss"

_HOLDINGS_LINK = re.compile(
    r'href=["\'](https://rigaku-holdings\.com/english/news/'
    r'(?P<cat>[a-z0-9-]+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<slug>[^/"\']+)/?)["\']',
    re.I,
)
_COM_LINK = re.compile(
    r'href=["\'](?P<path>/about/news-and-press-releases/[^?"\']+)(?:\?[^"\']*)?["\']'
    r'[^>]*>(?P<title>[^<]{8,240})</a>',
    re.I,
)
_HOLDINGS_TITLE = re.compile(r"<p>(.*?)</p>", re.I | re.S)


def _strip_html(text: str) -> str:
    out: list[str] = []
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
    return " ".join(unescape("".join(out)).split())


def _slug_title(slug: str) -> str:
    text = unescape(slug.replace("-", " ")).strip()
    text = re.sub(r"\s+", " ", text)
    if text.lower().startswith("press releaserigaku"):
        text = "Press Release: Rigaku" + text[19:]
    elif text.lower().startswith("press release"):
        text = "Press Release" + text[13:]
    return text[:220].title() if text.islower() else text[:220]


def parse_rigaku_holdings_html(html: str) -> list[RawItem]:
    items: list[RawItem] = []
    seen: set[str] = set()
    for match in _HOLDINGS_LINK.finditer(html):
        url = match.group(1).rstrip("/") + "/"
        if url in seen:
            continue
        seen.add(url)
        cat = match.group("cat")
        date_s = match.group("date")
        slug = match.group("slug")
        published = None
        try:
            published = datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=timezone.utc).replace(tzinfo=None)
        except ValueError:
            published = None
        # Title lives in <p>…</p> inside the same <a> block
        window = html[match.end() : match.end() + 700]
        title_m = _HOLDINGS_TITLE.search(window)
        title = _strip_html(title_m.group(1)) if title_m else _slug_title(slug)
        if not title:
            title = _slug_title(slug)
        items.append(
            RawItem(
                source="vendor",
                source_id=f"rigaku-holdings:{date_s}:{slug}"[:400],
                url=url,
                title=f"[理学 Rigaku] {title}",
                kind="vendor",
                raw_summary=f"Rigaku Holdings · {cat} · {date_s}",
                authors=["理学 Rigaku"],
                published_at=published,
                extra={
                    "track": "xray",
                    "vendor": "rigaku",
                    "topics": ["专业·X射线", "理学", "厂商动态", cat],
                },
                source_urls=[{"label": "理学 Rigaku", "url": url}],
            )
        )
        if len(items) >= 25:
            break
    return items


def parse_rigaku_com_html(html: str, base: str = "https://rigaku.com") -> list[RawItem]:
    items: list[RawItem] = []
    seen: set[str] = set()
    for match in _COM_LINK.finditer(html):
        path = match.group("path")
        if path.rstrip("/") == "/about/news-and-press-releases":
            continue
        url = urljoin(base, path.split("?")[0])
        if url in seen:
            continue
        seen.add(url)
        slug = urlparse(url).path.rstrip("/").split("/")[-1]
        title = _strip_html(match.group("title")) or _slug_title(slug)
        items.append(
            RawItem(
                source="vendor",
                source_id=f"rigaku-com:{slug}"[:400],
                url=url,
                title=f"[理学 Rigaku] {title}",
                kind="vendor",
                raw_summary="Rigaku product / press page",
                authors=["理学 Rigaku"],
                published_at=None,
                extra={
                    "track": "xray",
                    "vendor": "rigaku",
                    "topics": ["专业·X射线", "理学", "厂商动态"],
                },
                source_urls=[{"label": "理学 Rigaku", "url": url}],
            )
        )
        if len(items) >= 20:
            break
    return items


def parse_kla_feed(xml_text: str) -> list[RawItem]:
    parsed = feedparser.parse(xml_text)
    items: list[RawItem] = []
    for entry in parsed.entries[:25]:
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
                source="vendor",
                source_id=str(entry.get("id") or url)[:400],
                url=url,
                title=f"[科磊 KLA] {title}",
                kind="vendor",
                raw_summary=_strip_html(summary)[:3000],
                authors=["科磊 KLA"],
                published_at=published,
                extra={
                    "track": "xray",
                    "vendor": "kla",
                    "topics": ["专业·X射线", "科磊", "厂商动态", "半导体"],
                },
                source_urls=[{"label": "科磊 KLA", "url": url}],
            )
        )
    return items


def tag_pro_papers(items: list[RawItem]) -> list[RawItem]:
    out: list[RawItem] = []
    for item in items:
        extra = dict(item.extra or {})
        topics = list(extra.get("topics") or [])
        for tag in ("专业·X射线", "CD-SAXS", "XRD", "HRXRD"):
            if tag not in topics:
                topics.append(tag)
        extra["topics"] = topics
        extra["track"] = "xray"
        out.append(
            RawItem(
                source="arxiv_pro",
                source_id=item.source_id,
                url=item.url,
                title=item.title,
                kind="pro_paper",
                raw_summary=item.raw_summary,
                authors=item.authors,
                published_at=item.published_at,
                extra=extra,
                source_urls=item.source_urls,
            )
        )
    return out


async def collect_arxiv_pro(client: httpx.AsyncClient) -> list[RawItem]:
    params = {
        "search_query": ARXIV_PRO_QUERY,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": "40",
    }
    resp = await client.get(ENDPOINT, params=params, headers={"Accept": "application/atom+xml"})
    resp.raise_for_status()
    return tag_pro_papers(parse_arxiv_feed(resp.text, source="arxiv_pro"))


async def collect_vendors(client: httpx.AsyncClient) -> list[RawItem]:
    out: list[RawItem] = []
    accept_html = {"Accept": "text/html,application/xhtml+xml"}
    try:
        resp = await client.get(RIGAKU_HOLDINGS_NEWS, headers=accept_html)
        if resp.status_code < 400:
            out.extend(parse_rigaku_holdings_html(resp.text))
    except httpx.HTTPError:
        pass
    try:
        resp = await client.get(RIGAKU_COM_NEWS, headers=accept_html)
        if resp.status_code < 400:
            out.extend(parse_rigaku_com_html(resp.text))
    except httpx.HTTPError:
        pass
    try:
        resp = await client.get(
            KLA_PRESS_RSS,
            headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        if resp.status_code < 400:
            out.extend(parse_kla_feed(resp.text))
    except httpx.HTTPError:
        pass
    return out
