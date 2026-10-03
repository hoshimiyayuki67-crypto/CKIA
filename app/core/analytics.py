"""咨询数据分析（设计文档 第三章·6）。

匿名归集提问 -> 事项/环节/文件/时间/流失 五个维度 -> 《学生咨询热力图》报告。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryLog:
    """会话日志（匿名化，对应设计文档 第五章·数据结构设计）。"""

    session_hash: str
    question_text: str
    intent: str
    hit: bool
    answer_given: bool
    image_uploaded: bool = False
    feedback: str = ""
    log_date: str = field(default_factory=lambda: date.today().isoformat())


class Analytics:
    """提问匿名聚合，产出咨询热力图。"""

    def __init__(self) -> None:
        self.logs: list[QueryLog] = []

    def record(
        self,
        session_hash: str,
        question: str,
        intent: str,
        hit: bool,
        answer_given: bool,
        image_uploaded: bool = False,
    ) -> None:
        self.logs.append(
            QueryLog(
                session_hash=session_hash,
                question_text=question,
                intent=intent,
                hit=hit,
                answer_given=answer_given,
                image_uploaded=image_uploaded,
            )
        )

    def heatmap(self) -> dict:
        """生成咨询热力图：事项维度、时间维度、流失维度。"""
        by_category = Counter(log.intent for log in self.logs if log.intent)
        by_date = Counter(log.log_date for log in self.logs)
        miss_clusters = [log.question_text for log in self.logs if not log.hit]
        return {
            "category_ranking": by_category.most_common(),
            "date_distribution": dict(sorted(by_date.items())),
            "miss_clusters": miss_clusters,
        }


analytics = Analytics()


def record(
    session_hash: str,
    question: str,
    intent: str,
    hit: bool,
    answer_given: bool,
    image_uploaded: bool = False,
) -> None:
    """便捷入口：记录一条匿名提问日志。"""
    analytics.record(session_hash, question, intent, hit, answer_given, image_uploaded)
