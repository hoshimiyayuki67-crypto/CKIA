from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    issuer: str = Field(min_length=1)
    date: date
    doc_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    url: str | None = None


class Material(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item: str = Field(min_length=1)
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
    status: Literal["refusal", "card", "clarification"] = "refusal"
    message: str
    card: ActionCard | None = None
    sources: list[Source] = Field(default_factory=list)
    ai_generated: bool = True
    demo_mode: bool = False

    @model_validator(mode="after")
    def enforce_evidence(self):
        if self.status == "card":
            if self.card is None or self.sources != self.card.sources:
                raise ValueError("卡片必须绑定同一组真实检索出处")
        elif self.card is not None or self.sources:
            raise ValueError("拒答/澄清不得携带办理卡片或出处")
        return self
