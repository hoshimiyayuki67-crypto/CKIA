import re
import time
from collections import OrderedDict, deque
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from campus_assistant.repositories.accounts import AccountError

router = APIRouter()


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        if not re.fullmatch(r"[a-zA-Z0-9_]{3,32}", value):
            raise ValueError("用户名使用3至32位字母、数字或下划线")
        return value.lower()


class DeleteAccount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=8, max_length=128)


class SessionData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    school: dict = Field(max_length=3)
    category: str | None = Field(default=None, max_length=20)
    updated_at: str = Field(max_length=60)
    messages: list[dict] = Field(min_length=1, max_length=100)

    @field_validator("school")
    @classmethod
    def school_fields(cls, value):
        if (set(value) != {"id", "name", "domain"} or
                any(not isinstance(v, str) or not 1 <= len(v) <= 253 for v in value.values())):
            raise ValueError("院校信息不正确")
        return value


class SaveSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    data: SessionData


def repository(request: Request):
    if request.app.state.accounts is None:
        raise HTTPException(503, "账号服务尚未启用")
    return request.app.state.accounts


def invoke(operation, *args):
    try:
        return operation(*args)
    except AccountError as error:
        raise HTTPException(error.status, error.message) from None


def token(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer ") or len(authorization) > 200:
        raise HTTPException(401, "请先登录")
    return authorization[7:]


def current_user(request: Request, bearer: str = Depends(token)):
    return invoke(repository(request).user, bearer)


class AuthLimit:
    def __init__(self):
        self.clients = OrderedDict()
        self.total = deque()

    def check(self, client):
        now = time.monotonic()
        calls = self.clients.setdefault(client, deque())
        self.clients.move_to_end(client)
        for queue in (calls, self.total):
            while queue and queue[0] <= now - 60:
                queue.popleft()
        if len(calls) >= 10 or len(self.total) >= 60:
            raise HTTPException(429, "操作过于频繁，请稍后重试", headers={"Retry-After": "60"})
        calls.append(now)
        self.total.append(now)
        if len(self.clients) > 1024:
            self.clients.popitem(last=False)


def auth_limit(request: Request):
    peer = request.client.host if request.client else "unknown"
    request.app.state.auth_limit.check(peer)


@router.post("/auth/register", dependencies=[Depends(auth_limit)])
def register(payload: Credentials, request: Request):
    return invoke(repository(request).authenticate, payload.username, payload.password, True)


@router.post("/auth/login", dependencies=[Depends(auth_limit)])
def login(payload: Credentials, request: Request):
    return invoke(repository(request).authenticate, payload.username, payload.password)


@router.get("/auth/me")
def me(user: Annotated[dict, Depends(current_user)]):
    return user


@router.post("/auth/logout")
def logout(request: Request, bearer: str = Depends(token)):
    repository(request).logout(bearer)
    return {"ok": True}


@router.delete("/auth/account", dependencies=[Depends(auth_limit)])
def delete_account(payload: DeleteAccount, request: Request, user: Annotated[dict, Depends(current_user)]):
    invoke(repository(request).delete_account, user["id"], payload.password)
    return {"ok": True}


@router.get("/sessions")
def sessions(request: Request, user: Annotated[dict, Depends(current_user)]):
    return {"sessions": repository(request).list_sessions(user["id"])}


def valid_id(session_id):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", session_id):
        raise HTTPException(422, "对话编号不正确")


@router.put("/sessions/{session_id}")
def save(session_id: str, payload: SaveSession, request: Request, user: Annotated[dict, Depends(current_user)]):
    valid_id(session_id)
    return invoke(repository(request).save_session, user["id"], session_id, payload.revision,
                  payload.data.model_dump())


@router.delete("/sessions/{session_id}")
def delete(session_id: str, revision: int, request: Request, user: Annotated[dict, Depends(current_user)]):
    valid_id(session_id)
    return invoke(repository(request).save_session, user["id"], session_id, revision, None)
