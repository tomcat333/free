from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from app.collectors import RawItem

SOURCE_WEIGHT = {
    "arxiv": 48,
    "github": 46,
    "huggingface": 55,
    "hn": 50,
    "blog": 58,
    "reddit": 34,
}

KEYWORD_WEIGHTS = [
    (r"\bbreakthrough\b|\bsota\b|state[- ]of[- ]the[- ]art|刷新|突破|惊人", 14),
    (r"\bopen[- ]weight|\bopen[- ]source model|\bweights?\s+released|开源权重", 12),
    (r"\bworld model\b|\breasoning\b|\bagentic\b|\bmulti-agent\b", 10),
    (r"\bnew architecture\b|\btransformer\b|\bdiffusion\b|\bmamba\b|\bmoe\b", 8),
    (r"\bbenchmark\b|\bleaderboard\b|\bsurpass|\bbeat gpt|\bbeat claude", 10),
    (r"\brlhf\b|\bgrpo\b|\breinforcement learning\b", 6),
    (r"\bmultimodal\b|\bvideo generation\b|\brobotics\b", 6),
]


def score_item(raw: RawItem, now: datetime | None = None) -> tuple[float, list[str], str]:
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    reasons: list[str] = []
    score = float(SOURCE_WEIGHT.get(raw.source, 40))
    reasons.append(f"来源 {raw.source} +{SOURCE_WEIGHT.get(raw.source, 40)}")

    extra = raw.extra or {}
    engagement = 0.0
    if raw.kind == "repo":
        engagement = math.log1p(float(extra.get("stars") or 0)) * 7
        reasons.append(f"GitHub stars {extra.get('stars', 0)}")
    elif raw.source == "hn":
        engagement = math.log1p(float(extra.get("points") or 0)) * 8
        reasons.append(f"HN {extra.get('points', 0)} 分")
    elif raw.source == "reddit":
        engagement = math.log1p(float(extra.get("score") or 0)) * 6
        reasons.append(f"Reddit {extra.get('score', 0)} 分")
    elif raw.source == "huggingface":
        engagement = math.log1p(float(extra.get("upvotes") or extra.get("likes") or extra.get("trendingScore") or 0)) * 7
        reasons.append("Hugging Face 热度")
    score += engagement

    blob = f"{raw.title}\n{raw.raw_summary}".lower()
    hits = 0
    for pattern, weight in KEYWORD_WEIGHTS:
        if hits >= 3:
            break
        if re.search(pattern, blob, flags=re.I):
            score += weight
            hits += 1
            reasons.append(f"关键词 +{weight}")

    if raw.published_at:
        age_hours = max(0.0, (now - raw.published_at).total_seconds() / 3600)
        if age_hours <= 24:
            score += 10
            reasons.append("24 小时内 +10")
        elif age_hours <= 72:
            score += 6
            reasons.append("3 天内 +6")
        elif age_hours <= 168:
            score += 3
            reasons.append("一周内 +3")
        elif age_hours > 24 * 30:
            score -= 15
            reasons.append("超过一个月 -15")

    score = max(0.0, min(100.0, round(score, 1)))
    if score >= 82:
        tier = "breakthrough"
    elif score >= 62:
        tier = "notable"
    else:
        tier = "signal"
    return score, reasons, tier
