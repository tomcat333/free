from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawItem:
    source: str
    source_id: str
    url: str
    title: str
    kind: str
    raw_summary: str = ""
    authors: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    extra: dict = field(default_factory=dict)
    source_urls: list[dict] = field(default_factory=list)
