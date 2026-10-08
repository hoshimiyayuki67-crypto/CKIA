import json
from pathlib import Path

from campus_assistant.schemas.chat import ActionCard, ChatResponse
from campus_assistant.schemas.knowledge import KnowledgeEntry

TARGET = Path(__file__).resolve().parents[2] / "contracts"


def main():
    models = {
        "action-card": ActionCard,
        "chat-response": ChatResponse,
        "knowledge-entry": KnowledgeEntry,
    }
    for name, model in models.items():
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        schema.update(model.model_json_schema())
        (TARGET / f"{name}.schema.json").write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Exported {len(models)} contracts")


if __name__ == "__main__":
    main()
