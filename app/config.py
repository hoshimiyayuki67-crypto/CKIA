"""全局配置（读取 .env）。

对应设计文档 第五章·技术选型：接入 / 应用 / 智能 / 数据四层的可配置项。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """服务运行期配置。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- 接入层：微信公众号 / 企业微信 ----
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_token: str = ""
    wechat_aes_key: str = ""

    # ---- 智能层：模型服务 ----
    llm_api_base: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    rerank_model: str = "BAAI/bge-reranker-large"
    vision_model: str = "qwen-vl-max"

    # ---- 数据层：存储路径 ----
    vector_store_path: str = "./data/chroma"
    doc_store_path: str = "./data/docs"
    timeline_path: str = "./config/timeline.yaml"

    # ---- 检索参数 ----
    retrieval_top_k: int = 5
    relevance_threshold: float = 0.6      # 相关度闸门：低于该值触发拒答
    confidence_warn_threshold: float = 0.6  # 低于该值卡片附加"信息可能不完整"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
