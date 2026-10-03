"""意图识别与查询改写（设计文档 第三章·1 智能问答引擎、第六章·难点二）。"""
from __future__ import annotations

from dataclasses import dataclass

CATEGORIES: list[str] = ["资助", "教务", "财务", "学籍", "就业", "生活"]

# 校园场景口语-规范术语同义词表（设计文档 第六章·难点二）
SYNONYMS: dict[str, list[str]] = {
    "那个钱": ["资助", "助学金", "补助"],
    "贷款": ["生源地信用助学贷款"],
    "报账": ["费用报销"],
    "盖章": ["证明盖章"],
    "补考": ["缓考", "补考"],
}

# 拒答时提供的咨询渠道
REFUSAL_CONTACTS: dict[str, str] = {
    "资助": "学生资助管理中心",
    "教务": "教务处",
    "财务": "财务处",
    "学籍": "教务处 / 档案馆",
    "就业": "就业指导中心",
    "生活": "后勤处",
}


@dataclass
class Intent:
    category: str
    confidence: float


def classify(question: str, image: bytes | None = None) -> Intent:
    """① 意图识别：判断问题属于哪类事务。

    TODO 接入 LLM few-shot 分类或轻量分类模型；当前为占位实现。
    """
    return Intent(category="资助", confidence=0.0)


def rewrite(question: str) -> str:
    """② 查询改写：口语化提问改写为检索友好的规范查询。

    TODO 接入小模型改写；当前仅做同义词表扩充。
    """
    rewritten = question
    for spoken, terms in SYNONYMS.items():
        if spoken in rewritten:
            rewritten += " " + " ".join(terms)
    return rewritten


def refusal_contact(category: str) -> str:
    """返回该类别对应的咨询渠道。"""
    return REFUSAL_CONTACTS.get(category, "学校相关部门")
