from dataclasses import dataclass
from datetime import date
from pathlib import Path

from campus_assistant.schemas.knowledge import KnowledgeEntry


@dataclass(frozen=True)
class KnowledgeRepository:
    entries: tuple[KnowledgeEntry, ...] = ()

    @classmethod
    def load(cls, directory: Path):
        # 启动时完整校验。配置错误直接阻止启动，避免悄悄忽略坏资料。
        entries = tuple(
            KnowledgeEntry.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(directory.glob("*.json"))
        )
        keys = [(entry.source.doc_id, entry.source.chunk_id) for entry in entries]
        if len(keys) != len(set(keys)):
            raise ValueError("知识片段标识重复")
        return cls(entries)

    def eligible(self, today: date) -> list[KnowledgeEntry]:
        return [
            entry for entry in self.entries
            if entry.reviewed and entry.layer == "official"
            and entry.source.date <= today
            and (entry.valid_until is None or entry.valid_until >= today)
            and (entry.fields.deadline is None or entry.fields.deadline >= today)
        ]
