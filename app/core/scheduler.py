"""主动提醒调度（设计文档 第五章·4）。

组件：时间轴配置 + 调度器 + 订阅库 + 推送队列。
"""
from __future__ import annotations

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_scheduler = BackgroundScheduler()


def load_timeline() -> list[dict]:
    """加载学期时间轴配置。"""
    with open(settings.timeline_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def scan_timeline() -> list[dict]:
    """每日扫描时间轴，返回命中提醒条件的节点。

    TODO 依据 window 计算触发日期，并结合 remind_before 判断是否到达提醒日。
    """
    return []


def push_reminders(nodes: list[dict]) -> None:
    """向已订阅对应类别的用户分批推送提醒。

    TODO 接入订阅库（关注类别 + 免打扰设置）与推送队列，避免瞬时并发过高。
    """
    for node in nodes:
        logger.info("推送提醒：%s", node.get("name", ""))


def _daily_job() -> None:
    push_reminders(scan_timeline())


def start() -> None:
    """注册并启动每日调度任务。"""
    _scheduler.add_job(
        _daily_job, "cron", hour=9, minute=0, id="timeline_scan", replace_existing=True
    )
    _scheduler.start()


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
