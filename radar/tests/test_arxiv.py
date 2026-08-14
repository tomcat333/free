from app.collectors.arxiv import parse_arxiv_feed

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>Scaling World Models with Sparse MoE</title>
    <summary>We present a new architecture that beats prior SOTA.</summary>
    <published>2024-01-02T12:00:00Z</published>
    <author><name>Ada Lovelace</name></author>
    <link rel="alternate" href="https://arxiv.org/abs/2401.12345v1"/>
    <link title="pdf" href="https://arxiv.org/pdf/2401.12345v1" type="application/pdf"/>
    <category term="cs.LG"/>
  </entry>
</feed>
"""


def test_parse_arxiv_feed():
    items = parse_arxiv_feed(SAMPLE)
    assert len(items) == 1
    item = items[0]
    assert item.source_id.endswith("2401.12345v1") or "2401.12345" in item.source_id
    assert "World Models" in item.title
    assert item.kind == "paper"
    assert item.authors == ["Ada Lovelace"]
    assert item.extra["pdf"].endswith("2401.12345v1")
    assert any(s["label"] == "PDF" for s in item.source_urls)
