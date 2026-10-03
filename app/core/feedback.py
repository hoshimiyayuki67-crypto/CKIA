"""反馈收集（设计文档 附录A F-19）。每条回答下方提供「有用/没用」。"""
from __future__ import annotations

from collections import Counter

_counter: Counter[str] = Counter()


def record(message_id: str, useful: bool) -> None:
    """记录用户反馈。TODO 落库并关联到具体回答与事项类别。"""
    _counter["useful" if useful else "useless"] += 1


def summary() -> dict:
    """满意度汇总：反馈"有用"占总反馈的比例。"""
    total = sum(_counter.values())
    useful = _counter["useful"]
    return {
        "total": total,
        "useful": useful,
        "satisfaction": (useful / total) if total else 0.0,
    }
