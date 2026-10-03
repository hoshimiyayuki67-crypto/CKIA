"""视觉模型（智能层）。用于截图版面理解（Qwen-VL / GLM-4V）。"""
from __future__ import annotations

from app.config import settings


def describe(image: bytes, prompt: str) -> str:
    """调用视觉模型理解截图版面：标题、正文、表格、落款、公章与发布主体。

    TODO 接入 Qwen-VL / GLM-4V：图像 base64 编码后随 prompt 发送，
    返回结构化描述供 multimodal.understand 融合。
    """
    raise NotImplementedError(f"视觉模型 {settings.vision_model} 接口待接入")
