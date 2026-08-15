from datetime import datetime

from app.collectors.pro_xray import (
    parse_kla_feed,
    parse_rigaku_com_html,
    parse_rigaku_holdings_html,
    tag_pro_papers,
)
from app.collectors.arxiv import parse_arxiv_feed

HOLDINGS_HTML = """
<li>
  <a href="https://rigaku-holdings.com/english/news/corporate/2026-07-09/rigaku-opens-solutions-center/" class="over">
    <time datetime="2026-07-09">Jul 09, 2026</time>
    <span>Corporate</span>
    <p>[Press Release] Rigaku Opens Solutions Center for Semiconductor Metrology</p>
  </a>
</li>
<li>
  <a href="https://rigaku-holdings.com/english/news/product-technology/2025-12-18/onyx-3200/" class="over">
    <time datetime="2025-12-18">Dec 18, 2025</time>
    <span>Product</span>
    <p>[Press Release] Rigaku launches ONYX 3200</p>
  </a>
</li>
"""

COM_HTML = """
<tr>
  <td><a href="/about/news-and-press-releases/rigaku-launches-onyx-3200?hsLang=en">Rigaku launches ONYX 3200 for Semiconductor Manufacturing</a></td>
  <td>Semiconductors</td>
</tr>
"""

KLA_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>KLA Press</title>
    <item>
      <title>KLA Reports New Metrology Platform</title>
      <link>https://ir.kla.com/news-events/press-releases/detail/999/kla-reports-new-metrology</link>
      <guid>https://ir.kla.com/news-events/press-releases/detail/999</guid>
      <pubDate>Thu, 01 Jan 2026 12:00:00 GMT</pubDate>
      <description>Process control and semiconductor inspection update.</description>
    </item>
  </channel>
</rss>
"""

ARXIV_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2402.00001v1</id>
    <title>CD-SAXS metrology for semiconductor line gratings</title>
    <summary>High-resolution XRD and CD-SAXS for critical dimension control.</summary>
    <published>2024-02-01T12:00:00Z</published>
    <author><name>Test Author</name></author>
    <link rel="alternate" href="https://arxiv.org/abs/2402.00001v1"/>
    <link title="pdf" href="https://arxiv.org/pdf/2402.00001v1" type="application/pdf"/>
    <category term="cond-mat.mtrl-sci"/>
  </entry>
</feed>
"""


def test_parse_rigaku_holdings():
    items = parse_rigaku_holdings_html(HOLDINGS_HTML)
    assert len(items) == 2
    assert items[0].kind == "vendor"
    assert items[0].extra["vendor"] == "rigaku"
    assert "Semiconductor Metrology" in items[0].title
    assert items[0].published_at == datetime(2026, 7, 9)


def test_parse_rigaku_com():
    items = parse_rigaku_com_html(COM_HTML)
    assert len(items) == 1
    assert "ONYX 3200" in items[0].title
    assert items[0].url.endswith("rigaku-launches-onyx-3200")


def test_parse_kla_rss():
    items = parse_kla_feed(KLA_RSS)
    assert len(items) == 1
    assert items[0].extra["vendor"] == "kla"
    assert items[0].title.startswith("[科磊 KLA]")
    assert "Metrology" in items[0].title


def test_tag_pro_papers():
    raw = parse_arxiv_feed(ARXIV_SAMPLE)
    items = tag_pro_papers(raw)
    assert len(items) == 1
    assert items[0].source == "arxiv_pro"
    assert items[0].kind == "pro_paper"
    assert items[0].extra["track"] == "xray"
    assert "专业·X射线" in items[0].extra["topics"]
