"""FastAPI 应用入口（应用层）。

职责：装配路由、启动学期时间轴定时调度、暴露健康检查。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import chat, wechat
from app.config import settings
from app.core import scheduler
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 启动：注册并运行学期时间轴定时调度
    scheduler.start()
    logger.info("校园万事通服务启动，模型：%s", settings.llm_model)
    yield
    # 关闭：停止调度器，释放资源
    scheduler.shutdown()


app = FastAPI(
    title="校园万事通 API",
    description="微信里的校园事务智能体：智能问答 / 以图问图 / 结构化办事卡片 / 主动提醒",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router)     # 安卓 APP 客户端
app.include_router(wechat.router)   # 微信公众号 / 企业微信


@app.get("/health", tags=["系统"])
async def health() -> dict:
    """健康检查。"""
    return {"status": "ok", "service": "campus-agent", "version": app.version}
