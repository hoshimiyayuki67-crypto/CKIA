"""多模态截图理解（设计文档 第五章·2 多模态截图理解方案）。

采用文本通道（OCR）与视觉通道（版面理解）双通道并行，交叉验证。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScreenshotResult:
    text: str = ""                    # 文本通道：OCR 提取的文字
    layout: dict = field(default_factory=dict)  # 视觉通道：标题/正文/表格/公章/落款
    title: str = ""                  # 提取到的文件名
    issuer: str = ""                 # 发布部门
    date: str = ""                   # 发布日期
    confidence: float = 0.0


def understand(image: bytes, question: str | None = None) -> ScreenshotResult:
    """理解截图：预处理 -> 文本/视觉双通道 -> 融合判定。

    TODO 接入 Qwen-VL / GLM-4V 与 OCR：
    1) 图像预处理：自动裁边、纠偏、压缩；
    2) 文本通道：OCR 提取文字，保留阅读顺序；
    3) 视觉通道：识别标题、正文、表格、公章，判断发布主体；
    4) 融合：两通道一致性校验，冲突时以视觉通道版面归属为准。
    """
    return ScreenshotResult()


def compare_with_kb(result: ScreenshotResult) -> str:
    """关键标识（文件名+部门+日期）与知识库比对。

    返回差异提示；一致或无法判定时返回空串。
    TODO 接入知识库版本比对（设计文档 第五章·2 融合判定 第 3-4 步）。
    """
    return ""
