from app.free_bridge import build_free_prompt, extract_arxiv_id, format_free_intro, free_bridge_payload
from app.models import Item


def test_extract_arxiv_id_from_url():
    item = Item(
        source="huggingface",
        source_id="paper:2408.11562",
        url="https://huggingface.co/papers/2408.11562",
        title="S2R",
        kind="paper",
        extra_json='{"arxiv_id":"2408.11562"}',
    )
    assert extract_arxiv_id(item) == "2408.11562"


def test_free_prompt_and_bridge_payload():
    item = Item(
        id=1,
        source="arxiv",
        source_id="2401.00001",
        url="https://arxiv.org/abs/2401.00001",
        title="A paper about diffusion",
        kind="paper",
        authors="Ada",
        raw_summary="We remove reflections from video.",
        extra_json="{}",
        score=80,
        score_reasons="t",
        tier="notable",
        tags="paper",
        brief="brief",
        intro="",
        deep_dive="",
        sources_json="[]",
    )
    prompt = build_free_prompt(item, mode="deep")
    assert "问题背景" in prompt
    assert "2401.00001" in prompt or "arxiv.org" in prompt
    pack = free_bridge_payload(item)
    assert pack["pdf_url"].endswith(".pdf")
    assert any(c["id"] == "kimi" for c in pack["chats"])
    assert "Ollama" in pack["ollama_hint"]


def test_format_free_intro():
    text = format_free_intro(
        {
            "tldr": "A short free summary.",
            "abstract": "Longer abstract.",
            "paper_url": "https://www.semanticscholar.org/paper/x",
        }
    )
    assert "不消耗 API token" in text
    assert "A short free summary." in text
