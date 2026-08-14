from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp())
os.environ["DATA_DIR"] = str(_TMP)

import pytest
from fastapi.testclient import TestClient

from app.db import engine, init_db
from app.main import app
from app.models import Base, Item
from app.db import SessionLocal


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(engine)
    init_db()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def add_item(session, **kwargs) -> Item:
    item = Item(
        source=kwargs.get("source", "arxiv"),
        source_id=kwargs.get("source_id", "x"),
        url=kwargs.get("url", "https://example.com/x"),
        title=kwargs.get("title", "A new world model"),
        kind=kwargs.get("kind", "paper"),
        authors=kwargs.get("authors", "Ada"),
        raw_summary=kwargs.get("raw_summary", "We propose a breakthrough SOTA architecture."),
        extra_json=kwargs.get("extra_json", "{}"),
        score=kwargs.get("score", 88),
        score_reasons=kwargs.get("score_reasons", "test"),
        tier=kwargs.get("tier", "breakthrough"),
        tags=kwargs.get("tags", "paper"),
        brief=kwargs.get("brief", "一条测试简报"),
        intro=kwargs.get("intro", ""),
        deep_dive=kwargs.get("deep_dive", ""),
        sources_json=kwargs.get("sources_json", "[]"),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
