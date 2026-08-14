from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Item

log = logging.getLogger(__name__)

BRIEF_PROMPT = """你是前沿科技情报编辑。根据材料写两层中文简报，严格输出 JSON：
{{
  "brief": "不超过 80 字的一句话，让人扫一眼就知道发生了什么",
  "intro": "300-600 字深度介绍：这是什么、为什么现在重要、和已有工作差在哪、谁该关心、已知局限",
  "tags": ["标签1", "标签2"]
}}
不要编造论文里没有的实验结果。材料如下：
标题: {title}
类型: {kind}
来源: {source}
作者: {authors}
摘要/描述:
{summary}
"""

DEEP_PROMPT = """你是算法/系统讲解员。请用中文把下面这条前沿资讯讲透，输出 Markdown，包含：
1. 问题背景：它要解决什么
2. 全过程 / 方法步骤：尽量按流水线写清楚（数据、模型、训练、推理、评测）
3. 关键创新点：和旧方法差在哪
4. 怎么自己上手：仓库/论文怎么读、最小复现路径
5. 风险与未知：别吹过头
如果材料不足以写某节，就明确写「材料不足」。
标题: {title}
类型: {kind}
来源: {source}
链接: {url}
摘要:
{summary}
附加:
{extra}
"""


async def enrich_items(session: Session, items: list[Item], deep: bool = False) -> int:
    if not items:
        return 0
    if not settings.llm_enabled:
        for item in items:
            if not item.intro:
                item.intro = _template_intro(item)
            if deep and not item.deep_dive:
                item.deep_dive = _template_deep(item)
        session.commit()
        return len(items)

    done = 0
    async with httpx.AsyncClient(timeout=90.0) as client:
        for item in items:
            try:
                data = await _chat_json(client, BRIEF_PROMPT.format(
                    title=item.title,
                    kind=item.kind,
                    source=item.source,
                    authors=item.authors,
                    summary=(item.raw_summary or "")[:4000],
                ))
                if data.get("brief"):
                    item.brief = str(data["brief"]).strip()
                if data.get("intro"):
                    item.intro = str(data["intro"]).strip()
                if data.get("tags"):
                    item.tags = ",".join(str(t) for t in data["tags"][:10])
                if deep:
                    item.deep_dive = await _chat_text(client, DEEP_PROMPT.format(
                        title=item.title,
                        kind=item.kind,
                        source=item.source,
                        url=item.url,
                        summary=(item.raw_summary or "")[:5000],
                        extra=item.extra_json[:2000],
                    ))
                item.enriched_at = datetime.now(timezone.utc).replace(tzinfo=None)
                done += 1
                session.commit()
            except Exception:
                log.exception("enrich failed for item %s", item.id)
                if not item.intro:
                    item.intro = _template_intro(item)
                session.commit()
    return done


async def ensure_deep_dive(session: Session, item: Item) -> Item:
    if item.deep_dive:
        return item
    await enrich_items(session, [item], deep=True)
    session.refresh(item)
    return item


async def _chat_json(client: httpx.AsyncClient, prompt: str) -> dict:
    text = await _chat_text(client, prompt)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


async def _chat_text(client: httpx.AsyncClient, prompt: str) -> str:
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    resp = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": "你是严谨的中文科技情报编辑，不编造事实。"},
                {"role": "user", "content": prompt},
            ],
        },
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _template_intro(item: Item) -> str:
    extra = {}
    try:
        extra = json.loads(item.extra_json or "{}")
    except json.JSONDecodeError:
        extra = {}
    bits = [
        f"**{item.title}** 被雷达标为「{item.tier}」（{item.score} 分）。",
        f"类型：{item.kind}；来源：{item.source}。",
    ]
    if item.authors:
        bits.append(f"相关人/机构：{item.authors}。")
    if item.raw_summary:
        bits.append("原始摘要：")
        bits.append(item.raw_summary[:1200])
    if extra:
        bits.append("采集侧信号：" + ", ".join(f"{k}={v}" for k, v in list(extra.items())[:8]))
    bits.append("尚未配置大模型，以上为结构化整理。配置 OPENAI_API_KEY 后可自动写深度介绍与全过程。")
    return "\n\n".join(bits)


def _template_deep(item: Item) -> str:
    return (
        f"# {item.title}\n\n"
        f"## 问题背景\n材料来自 {item.source}，类型 {item.kind}。\n\n"
        f"## 原文要点\n{item.raw_summary or '（无摘要）'}\n\n"
        f"## 怎么上手\n打开来源链接阅读，并视情况克隆仓库或下载论文 PDF。\n\n"
        f"## 材料不足\n配置 OpenAI 兼容接口后，可生成逐步算法/系统讲解。\n"
    )
