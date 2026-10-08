import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from campus_assistant.api.chat import router
from campus_assistant.intelligence.deepseek import DeepSeek
from campus_assistant.intelligence.web_search import TavilySearch, WebSearch
from campus_assistant.repositories.knowledge import KnowledgeRepository
from campus_assistant.services.ai_answer import CallLimit

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parent


def create_app(
    repository: KnowledgeRepository | None = None, demo_mode: bool = False,
    model: DeepSeek | None = None,
    search: WebSearch | None = None,
) -> FastAPI:
    application = FastAPI(title="校园万事通", version="0.4.0")
    application.state.knowledge = repository if repository is not None else KnowledgeRepository()
    application.state.demo_mode = demo_mode
    application.state.model = model
    application.state.search = search if search is not None else WebSearch()
    application.state.call_limit = CallLimit()
    application.include_router(router, prefix="/api/v1")

    @application.get("/health")
    async def health():
        return {
            "status": "ok",
            "knowledge_status": "loaded" if application.state.knowledge.entries else "not_configured",
            "demo_mode": demo_mode,
            "ai_status": "configured" if model else "disabled",
            "ai_model": model.model if model else None,
            "search_provider": "tavily" if isinstance(application.state.search, TavilySearch)
                               else "bing-rss-best-effort",
            "search_status": "configured" if getattr(application.state.search, "_key", "")
                             else "not_configured",
        }

    if (PROJECT / "web").is_dir():
        application.mount("/web", StaticFiles(directory=PROJECT / "web"), name="web")

        @application.get("/", include_in_schema=False)
        async def index():
            return FileResponse(PROJECT / "web" / "index.html")

    return application


demo = os.getenv("CAMPUS_DEMO") == "1"
directory = ROOT / "examples" if demo else Path(
    os.getenv("CAMPUS_KNOWLEDGE_DIR", str(PROJECT / "knowledge" / "processed"))
)
if "CAMPUS_KNOWLEDGE_DIR" in os.environ and not directory.is_dir():
    raise ValueError("CAMPUS_KNOWLEDGE_DIR 目录不存在")
app = create_app(
    KnowledgeRepository.load(directory), demo_mode=demo, model=DeepSeek.from_environment(),
    search=WebSearch.from_environment(),
)
