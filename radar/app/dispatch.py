from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Dispatch, Item


def build_run_pack(item: Item) -> dict:
    extra = {}
    try:
        extra = json.loads(item.extra_json or "{}")
    except json.JSONDecodeError:
        extra = {}
    clone = extra.get("clone_url") or ""
    if item.kind == "repo" and item.url.startswith("https://github.com/") and not clone:
        clone = item.url.rstrip("/") + ".git"
    commands = _commands(item, extra, clone)
    prompt = _agent_prompt(item, extra, clone, commands)
    return {
        "event": "frontier.dispatch",
        "item_id": item.id,
        "title": item.title,
        "kind": item.kind,
        "url": item.url,
        "clone_url": clone,
        "pdf": extra.get("pdf") or "",
        "suggested_commands": commands,
        "agent_prompt": prompt,
        "brief": item.brief,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def dispatch_item(session: Session, item: Item) -> Dispatch:
    pack = build_run_pack(item)
    status = "prepared"
    response_text = ""
    if settings.dispatch_webhook_url:
        headers = {"Content-Type": "application/json"}
        if settings.dispatch_token:
            headers["Authorization"] = f"Bearer {settings.dispatch_token}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(settings.dispatch_webhook_url, headers=headers, json=pack)
                response_text = (resp.text or "")[:4000]
                status = "sent" if resp.status_code < 300 else "webhook_error"
        except httpx.HTTPError as exc:
            status = "webhook_error"
            response_text = str(exc)
    row = Dispatch(
        item_id=item.id,
        status=status,
        pack_json=json.dumps(pack, ensure_ascii=False),
        response_text=response_text,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _commands(item: Item, extra: dict, clone: str) -> list[str]:
    if item.kind == "repo" or clone:
        repo_dir = (item.title.split("/")[-1] if "/" in item.title else "repo").replace(" ", "-")
        return [
            f"git clone {clone or item.url}",
            f"cd {repo_dir}",
            "ls",
            "# 阅读 README 后按项目说明安装并跑最小示例",
        ]
    if extra.get("pdf") or item.kind == "paper":
        pdf = extra.get("pdf") or (item.url.replace("/abs/", "/pdf/") + ".pdf")
        return [
            f"# 论文: {item.url}",
            f"# PDF: {pdf}",
            "# 可把 agent_prompt 发给远程机器上的编码代理去复现",
        ]
    return [f"# 打开 {item.url} 阅读，并按页面说明试用"]


def _agent_prompt(item: Item, extra: dict, clone: str, commands: list[str]) -> str:
    return (
        f"请在一台有网络的机器上尝试理解并最小复现下面这条前沿工作，不要做破坏性操作。\n"
        f"标题: {item.title}\n"
        f"链接: {item.url}\n"
        f"类型: {item.kind}\n"
        f"摘要: {(item.raw_summary or item.brief)[:1500]}\n"
        f"克隆: {clone or '无'}\n"
        f"建议命令:\n" + "\n".join(commands) + "\n"
        f"完成后告诉我：环境需求、能否跑通、关键结果、失败原因。"
    )
