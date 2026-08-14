from app.collectors import RawItem
from app.models import Item
from app.pipeline.ingest import ingest_raw_items


def test_ingest_dedupes_by_url(session):
    raw = RawItem(
        source="hn",
        source_id="1",
        url="https://github.com/acme/x",
        title="acme/x",
        kind="repo",
        raw_summary="first",
        extra={"points": 10},
    )
    created = ingest_raw_items(session, {"hn": [raw]})
    assert len(created) == 1
    again = ingest_raw_items(session, {"github": [raw]})
    assert again == []
    assert session.query(Item).count() == 1
