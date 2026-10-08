from fastapi import FastAPI

from campus_assistant.api.chat import router

app = FastAPI(title="校园万事通", version="0.1.0")
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "knowledge_status": "not_configured"}
