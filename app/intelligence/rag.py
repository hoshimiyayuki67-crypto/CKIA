"""RAG 检索增强生成链路（设计文档 第五章·3）。

链路：意图识别 -> 查询改写 -> 混合检索 -> 重排序 -> 相关度闸门
      -> 受限生成 -> 字段抽取与校验 -> 卡片组装。
"""
from __future__ import annotations

from app.config import settings
from app.core import card as card_builder
from app.core import extractor
from app.core import intent as intent_mod
from app.core import multimodal
from app.core.intent import refusal_contact
from app.intelligence import llm, prompts, retriever
from app.schemas.card import ActionCard, Refusal
from app.utils.logger import get_logger

logger = get_logger(__name__)


def answer(question: str, image: bytes | None = None) -> ActionCard | Refusal | str:
    """校园事务问答主链路。"""
    # 以图问图：先理解截图，并做版本差异比对
    if image is not None:
        shot = multimodal.understand(image, question)
        diff = multimodal.compare_with_kb(shot)
        if diff:
            return diff  # 主动提示截图与现行文件可能存在出入
        question = question or shot.title

    # ① 意图识别
    intent = intent_mod.classify(question, image=image)
    # ② 查询改写
    query = intent_mod.rewrite(question)
    # ③ 混合检索（双层知识库，官方层优先）
    hits = retriever.hybrid_search(query, category=intent.category)
    # ④ 重排序
    hits = retriever.rerank(query, hits)
    # ⑤ 相关度闸门：低于阈值直接拒答，不给模型发挥空间
    if retriever.top_score(hits) < settings.relevance_threshold:
        return refusal(intent.category)

    try:
        # ⑥ 受限生成（仅依据检索片段）
        draft = llm.generate(prompts.RAG_SYSTEM_PROMPT, question=question, context=hits)
        # ⑦ 字段抽取与校验
        fields = extractor.validate(extractor.extract(draft, hits))
        # ⑧ 卡片组装
        return card_builder.build_card(fields, sources=hits)
    except Exception:  # 降级：任一环节失败，保证输出带出处的纯文本答案
        logger.exception("生成/抽取失败，降级为纯文本回答")
        return _fallback_text(hits)


def refusal(category: str) -> Refusal:
    """拒答并给出咨询渠道，让用户不至于无功而返。"""
    contact = refusal_contact(category)
    return Refusal(
        intent=category,
        message=f"未查询到相关规定，建议咨询{contact}。",
        contact=contact,
    )


def _fallback_text(hits) -> str:
    """降级输出：带出处的纯文本答案。"""
    lines = ["未能生成结构化卡片，以下为依据原文的参考信息："]
    for hit in hits:
        lines.append(f"· {hit.chunk_text}")
        lines.append(f"  出处：《{hit.title}》{hit.issuer}")
    return "\n".join(lines)
