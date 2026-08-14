from app.collectors.github import parse_github_search
from app.collectors.hn import parse_hn
from app.collectors.huggingface import parse_daily_papers, parse_models
from app.collectors.reddit import parse_reddit_listing, parse_reddit_rss


def test_parse_hn():
    payload = {
        "hits": [
            {
                "objectID": "42",
                "title": "Open-weight reasoning model",
                "url": "https://example.com/model",
                "points": 120,
                "num_comments": 33,
                "author": "pg",
                "created_at": "2024-02-01T00:00:00.000Z",
            }
        ]
    }
    items = parse_hn(payload)
    assert items[0].source_id == "42"
    assert items[0].extra["points"] == 120
    assert any("news.ycombinator.com" in s["url"] for s in items[0].source_urls)


def test_parse_github_search():
    payload = {
        "items": [
            {
                "id": 9,
                "full_name": "acme/world-model",
                "html_url": "https://github.com/acme/world-model",
                "description": "SOTA world model",
                "stargazers_count": 88,
                "forks_count": 3,
                "language": "Python",
                "topics": ["llm"],
                "created_at": "2024-03-01T00:00:00Z",
                "pushed_at": "2024-03-02T00:00:00Z",
                "clone_url": "https://github.com/acme/world-model.git",
                "default_branch": "main",
                "owner": {"login": "acme"},
            }
        ]
    }
    items = parse_github_search(payload)
    assert items[0].kind == "repo"
    assert items[0].extra["stars"] == 88
    assert items[0].extra["clone_url"].endswith(".git")


def test_parse_hf_papers_and_models():
    papers = parse_daily_papers(
        [
            {
                "publishedAt": "2024-04-01T00:00:00.000Z",
                "paper": {
                    "id": "2404.00001",
                    "title": "Better Transformers",
                    "summary": "abstract",
                    "authors": [{"name": "A"}],
                    "upvotes": 12,
                },
            }
        ]
    )
    assert papers[0].kind == "paper"
    assert papers[0].url.endswith("/papers/2404.00001")
    models = parse_models(
        [{"id": "acme/cool-llm", "likes": 10, "downloads": 100, "trendingScore": 9, "pipeline_tag": "text-generation"}]
    )
    assert models[0].kind == "model"
    assert models[0].title == "acme/cool-llm"


def test_parse_reddit():
    payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc",
                        "title": "New local model",
                        "stickied": False,
                        "permalink": "/r/LocalLLaMA/comments/abc/x",
                        "score": 400,
                        "num_comments": 20,
                        "author": "u1",
                        "created_utc": 1_700_000_000,
                        "selftext": "runs on 24GB",
                        "url": "https://github.com/x/y",
                    }
                }
            ]
        }
    }
    items = parse_reddit_listing(payload, "LocalLLaMA")
    assert items[0].extra["subreddit"] == "LocalLLaMA"
    assert items[0].extra["score"] == 400


def test_parse_reddit_rss_skips_automod():
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>t3_skip</id>
        <title>[D] Self-Promotion Thread</title>
        <link href="https://www.reddit.com/r/MachineLearning/comments/skip"/>
        <author><name>/u/AutoModerator</name></author>
      </entry>
      <entry>
        <id>t3_keep</id>
        <title>[R] A surprising optimizer</title>
        <link href="https://www.reddit.com/r/MachineLearning/comments/keep"/>
        <author><name>/u/researcher</name></author>
        <summary>beats Adam</summary>
        <published>2024-01-01T00:00:00Z</published>
      </entry>
    </feed>
    """
    items = parse_reddit_rss(xml, "MachineLearning")
    assert len(items) == 1
    assert items[0].title.startswith("[R]")
