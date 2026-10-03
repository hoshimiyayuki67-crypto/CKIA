"""大语言模型封装（智能层）。

兼容 OpenAI 协议，可切换 DeepSeek / 通义千问等国内直连服务。
"""
from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.schemas.knowledge import RetrievedChunk

_client = OpenAI(base_url=settings.llm_api_base, api_key=settings.llm_api_key or "EMPTY")


def generate(system_prompt: str, question: str, context: list[RetrievedChunk]) -> str:
    """受限生成：仅依据给定参考资料作答，返回 JSON 草稿。

    模型调用失败时抛异常，由上层（rag.answer）降级为带出处的纯文本答案。
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": _compose(question, context)},
    ]
    resp = _client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


def _compose(question: str, context: list[RetrievedChunk]) -> str:
    """将检索片段编号后拼入提示词，支撑出处一一对应。"""
    blocks = [f"[{i + 1}] {c.chunk_text}" for i, c in enumerate(context)]
    body = "\n".join(blocks) if blocks else "（无）"
    return f"参考资料：\n{body}\n\n学生提问：{question}"
