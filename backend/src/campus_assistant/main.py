import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from campus_assistant.api.accounts import AuthLimit
from campus_assistant.api.accounts import router as accounts_router
from campus_assistant.api.chat import router
from campus_assistant.intelligence.deepseek import DeepSeek
from campus_assistant.intelligence.web_search import TavilySearch, WebSearch
from campus_assistant.repositories.accounts import Accounts
from campus_assistant.repositories.knowledge import KnowledgeRepository
from campus_assistant.services.ai_answer import CallLimit

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parent


def create_app(
    repository: KnowledgeRepository | None = None, demo_mode: bool = False,
    model: DeepSeek | None = None,
    search: WebSearch | None = None,
    accounts: Accounts | None = None,
) -> FastAPI:
    application = FastAPI(title="校园万事通", version="1.0.0")
    application.state.accounts = accounts
    application.state.auth_limit = AuthLimit()
    application.state.knowledge = repository if repository is not None else KnowledgeRepository()
    application.state.demo_mode = demo_mode
    application.state.model = model
    application.state.search = search if search is not None else WebSearch()
    application.state.call_limit = CallLimit()
    application.include_router(router, prefix="/api/v1")
    application.include_router(accounts_router, prefix="/api/v1")

    @application.get('/api/v1/documents/imuchuangye-handbook-2021')
    async def handbook_original():
        # User explicitly approved publishing this original handbook and its chunks.
        from fastapi import HTTPException
        files = list((PROJECT / 'knowledge' / 'official').glob('*2021*.doc'))
        if not files:
            raise HTTPException(404, '手册原文件未部署')
        return FileResponse(files[0], media_type='application/msword', filename='student-handbook-2021.doc')

    @application.middleware("http")
    async def bounded_body(request, call_next):
        if request.method in {"POST", "PUT", "DELETE"}:
            limit = 4096 if request.url.path.startswith("/api/v1/auth/") else 262144
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > limit:
                    return JSONResponse({"detail": "请求内容过大"}, status_code=413)
            request._body = bytes(raw)
        response = await call_next(request)
        if request.url.path.startswith(("/api/v1/auth", "/api/v1/sessions")):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/health")
    async def health():
        return {
            "status": "ok",
            "accounts_status": "configured" if accounts else "disabled",
            "knowledge_status": "loaded" if (application.state.knowledge.entries or application.state.knowledge.documents) else "not_configured",
            "document_chunks": len(application.state.knowledge.documents),
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
    accounts=Accounts(Path(os.environ["CAMPUS_DATA_DIR"]) / "accounts.sqlite3")
    if os.getenv("CAMPUS_DATA_DIR") else None,
)
