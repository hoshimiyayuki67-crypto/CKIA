"""统一日志。"""
from __future__ import annotations

import logging

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """获取带统一格式的 logger。"""
    _configure()
    return logging.getLogger(name)
