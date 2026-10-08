from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from campus_assistant.schemas.chat import Category, Material, Source

UNKNOWN = "未查到明确信息，请向相关部门确认"
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CardFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matter_name: NonEmptyText
    target_users: list[NonEmptyText] = Field(min_length=1)
    materials: list[Material] = Field(min_length=1)
    location: str | None = None
    office_hours: str | None = None
    deadline: date | None = None
    channel: str | None = None
    contact: str | None = None
    notes: list[str] = Field(default_factory=list)


class KnowledgeEntry(BaseModel):
    """人工结构化记录；可执行字段必须逐字出现在对应片段中。"""

    model_config = ConfigDict(extra="forbid")
    source: Source
    category: Category
    layer: Literal["official", "experience"]
    version: str = Field(min_length=1)
    reviewed: bool = False
    valid_until: date | None = None
    chunk_text: str = Field(min_length=1)
    aliases: list[NonEmptyText] = Field(min_length=1)
    fields: CardFields

    @model_validator(mode="after")
    def validate_extracted_fields(self):
        fields = self.fields
        claims = [fields.matter_name, *fields.target_users, *fields.notes]
        claims.extend(item.item for item in fields.materials)
        claims.extend(item.note for item in fields.materials if item.note)
        claims.extend(
            value for value in (
                fields.location, fields.office_hours, fields.channel, fields.contact
            ) if value
        )
        if fields.deadline:
            claims.append(fields.deadline.isoformat())
        if any(claim not in self.chunk_text for claim in claims):
            raise ValueError("抽取字段不在来源片段中")
        return self
