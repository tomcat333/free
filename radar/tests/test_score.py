from datetime import datetime, timedelta, timezone

from app.collectors import RawItem
from app.pipeline.score import score_item


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _raw(**kwargs) -> RawItem:
    defaults = dict(
        source="arxiv",
        source_id="2401.00001",
        url="https://arxiv.org/abs/2401.00001",
        title="A paper",
        kind="paper",
        raw_summary="ordinary work",
        published_at=_now(),
        extra={},
    )
    defaults.update(kwargs)
    return RawItem(**defaults)


def test_official_blog_scores_high():
    score, _reasons, tier = score_item(_raw(source="blog", title="OpenAI releases new model", kind="news"))
    assert score >= 60
    assert tier in {"notable", "breakthrough"}


def test_breakthrough_keywords_and_freshness():
    score, reasons, tier = score_item(
        _raw(
            title="A breakthrough SOTA world model",
            raw_summary="open-weight reasoning model beats GPT",
            source="huggingface",
            extra={"upvotes": 80},
        )
    )
    assert score >= 82
    assert tier == "breakthrough"
    assert any("关键词" in r or "24" in r for r in reasons)


def test_old_low_engagement_stays_signal():
    score, _reasons, tier = score_item(
        _raw(
            source="reddit",
            title="weekly thread",
            raw_summary="chat",
            published_at=_now() - timedelta(days=40),
            extra={"score": 2},
        )
    )
    assert score < 60
    assert tier == "signal"


def test_github_stars_help():
    low, _, _ = score_item(_raw(source="github", kind="repo", extra={"stars": 3}, title="tiny"))
    high, _, _ = score_item(_raw(source="github", kind="repo", extra={"stars": 4000}, title="tiny"))
    assert high > low
