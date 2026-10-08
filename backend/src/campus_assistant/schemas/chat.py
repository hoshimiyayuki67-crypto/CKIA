from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["资助", "教务", "财务", "学籍", "就业", "生活"]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    category: Category | None = None

    @field_validator("question")
    @classmethod
    def nonblank_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value


class Source(BaseModel):
    title: str
    issuer: str
    date: date
    doc_id: str
    chunk_id: str
    url: str | None = None


class Material(BaseModel):
    item: str
    required: bool
    note: str | None = None


class ActionCard(BaseModel):
    matter_name: str
    target_users: list[str] = Field(min_length=1)
    materials: list[Material] = Field(min_length=1)
    location: str
    office_hours: str
    deadline: date | None = None
    channel: str
    contact: str
    sources: list[Source] = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class ChatResponse(BaseModel):
    status: Literal["refusal"] = "refusal"
    message: str
    card: None = None
    sources: list[Source] = Field(default_factory=list, max_length=0)
    ai_generated: bool = True
