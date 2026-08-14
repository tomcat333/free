import asyncio

from app.collectors import RawItem
from app.models import Item
from app.worker import collect_cycle


def test_collect_cycle_ingests_mocked_sources(monkeypatch, session):
    raw = RawItem(
        source="hn",
        source_id="99",
        url="https://example.com/new-algo",
        title="A surprising new optimizer",
        kind="discussion",
        raw_summary="beats Adam on LLM pretraining",
        extra={"points": 200},
    )

    async def fake_collect_all():
        return {"hn": [raw]}

    monkeypatch.setattr("app.worker.collect_all", fake_collect_all)
    result = asyncio.run(collect_cycle())
    assert result["new_items"] == 1
    assert session.query(Item).filter(Item.url == raw.url).one()
