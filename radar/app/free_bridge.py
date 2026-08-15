from __future__ import annotations

import json
import re
from urllib.parse import quote

import httpx

from app.config import settings
from app.models import Item

FREE_CHATS = [
    {
        "id": "deepseek",
        "label": "DeepSeek 网页版",
        "url": "https://chat.deepseek.com/",
        "hint": "打开后粘贴提示词（通常可免费使用）",
    },
    {
        "id": "kimi",
        "label": "Kimi 网页版",
        "url": "https://kimi.moonshot.cn/",
        "hint": "打开后粘贴提示词",
    },
    {
        "id": "doubao",
        "label": "豆包网页版",
        "url": "https://www.doubao.com/chat/",
        "hint": "打开后粘贴提示词",
    },
]


def extract_arxiv_id(item: Item) -> str:
    extra = {}
    try:
        extra = json.loads(item.extra_json or "{}")
    except json.JSONDecodeError:
        extra = {}
    if extra.get("arxiv_id"):
        return str(extra["arxiv_id"]).split("v")[0]
    for text in (item.source_id or "", item.url or ""):
        m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", text)
        if m:
            return m.group(1)
    return ""


def build_free_prompt(item: Item, *, mode: str = "deep") -> str:
    summary = (item.raw_summary or item.brief or "").strip()[:3500]
    if mode == "intro":
        ask = (
            "请用中文写：\n"
            "1) 不超过 80 字的一句话摘要\n"
            "2) 300-600 字深度介绍（是什么、为何重要、和旧工作差在哪、局限）\n"
            "不要编造材料里没有的实验结果。"
        )
    else:
        ask = (
            "请用中文直接输出 Markdown，不要开场白，包含：\n"
            "## 问题背景\n## 方法与流程\n## 关键创新点\n## 怎么上手\n## 局限与未知\n"
            "材料不够的小节写「本节仅有摘要级信息，细节需看原文」。"
        )
    return (
        f"{ask}\n\n"
        f"标题: {item.title}\n"
        f"类型: {item.kind}\n"
        f"来源: {item.source}\n"
        f"链接: {item.url}\n"
        f"作者: {item.authors}\n"
        f"摘要/描述:\n{summary or '（无摘要，请根据标题与链接理解）'}\n"
    )


def free_bridge_payload(item: Item) -> dict:
    arxiv_id = extract_arxiv_id(item)
    pdf = ""
    try:
        extra = json.loads(item.extra_json or "{}")
        pdf = extra.get("pdf") or ""
    except json.JSONDecodeError:
        pdf = ""
    if arxiv_id and not pdf:
        pdf = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return {
        "item_id": item.id,
        "title": item.title,
        "url": item.url,
        "arxiv_id": arxiv_id,
        "pdf_url": pdf,
        "prompt_intro": build_free_prompt(item, mode="intro"),
        "prompt_deep": build_free_prompt(item, mode="deep"),
        "chats": FREE_CHATS,
        "mailto": _mailto(item),
        "ollama_hint": (
            "本地免费：安装 Ollama 后，在 .env 设 "
            "OPENAI_BASE_URL=http://127.0.0.1:11434/v1 、OPENAI_API_KEY=ollama 、"
            "OPENAI_MODEL=qwen2.5:7b（或你已拉取的模型），即可零 API 费用。"
        ),
    }


def _mailto(item: Item) -> str:
    subject = quote(f"请解读：{item.title[:80]}")
    body = quote(build_free_prompt(item, mode="deep")[:1500])
    return f"mailto:?subject={subject}&body={body}"


async def fetch_semantic_scholar_tldr(item: Item) -> dict | None:
    """免费公开摘要（Semantic Scholar TLDR），不消耗你的大模型 token。"""
    arxiv_id = extract_arxiv_id(item)
    if not arxiv_id:
        return None
    url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}"
    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        resp = await client.get(url, params={"fields": "title,tldr,abstract,url"})
        if resp.status_code >= 400:
            return None
        data = resp.json()
    tldr = ((data.get("tldr") or {}).get("text") or "").strip()
    abstract = (data.get("abstract") or "").strip()
    if not tldr and not abstract:
        return None
    return {
        "source": "semantic_scholar",
        "paper_url": data.get("url") or f"https://www.semanticscholar.org/paper/{arxiv_id}",
        "tldr": tldr,
        "abstract": abstract[:2000],
    }


def format_free_intro(bundle: dict) -> str:
    bits = ["【免费公开摘要 · Semantic Scholar，不消耗 API token】"]
    if bundle.get("tldr"):
        bits.append(bundle["tldr"])
    if bundle.get("abstract"):
        bits.append("原文摘要：")
        bits.append(bundle["abstract"])
    if bundle.get("paper_url"):
        bits.append(f"来源：{bundle['paper_url']}")
    bits.append("若要更细的中文讲解，可用本页「免费网页解读」复制提示词，粘贴到 Kimi / 豆包 / DeepSeek 网页版。")
    return "\n\n".join(bits)
