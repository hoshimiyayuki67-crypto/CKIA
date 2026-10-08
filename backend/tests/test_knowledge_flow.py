import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from campus_assistant.main import ROOT, create_app
from campus_assistant.repositories.knowledge import KnowledgeRepository
from campus_assistant.schemas.chat import ChatRequest
from campus_assistant.schemas.knowledge import KnowledgeEntry
from campus_assistant.services.answer import answer


def record():
    return json.loads((ROOT / "examples/demo-library.json").read_text(encoding="utf-8"))


def respond(data, question="测试馆借阅需要什么材料？", category=None):
    repository = KnowledgeRepository((KnowledgeEntry.model_validate(data),))
    return answer(ChatRequest(question=question, category=category), repository, date(2026, 10, 8))


def test_verified_card_binds_actual_chunk():
    result = respond(record())
    assert result.status == "card"
    assert result.card.materials[0].item == "测试借阅卡"
    assert result.sources[0].chunk_id == "demo-library-1"
    assert result.card.sources == result.sources
    assert result.card.deadline is None


@pytest.mark.parametrize("changes", [
    {"reviewed": False}, {"layer": "experience"}, {"valid_until": "2026-10-07"},
])
def test_untrusted_or_expired_content_never_answers(changes):
    data = record()
    data.update(changes)
    result = respond(data)
    assert result.status == "refusal"
    assert not result.sources


def test_unrelated_or_wrong_category_refuses():
    assert respond(record(), "今天下雨吗？").status == "refusal"
    assert respond(record(), category="教务").status == "refusal"


def test_fabricated_field_rejected_at_ingestion():
    data = record()
    data["fields"]["location"] = "不存在的行政楼301"
    with pytest.raises(ValidationError, match="抽取字段不在来源片段中"):
        KnowledgeEntry.model_validate(data)


def test_ambiguous_hit_requests_clarification():
    first = KnowledgeEntry.model_validate(record())
    second = first.model_copy(deep=True)
    second.source.doc_id = "second"
    repository = KnowledgeRepository((first, second))
    result = answer(ChatRequest(question="测试借书"), repository, date(2026, 10, 8))
    assert result.status == "clarification"
    assert result.card is None


def test_future_source_not_used():
    data = record()
    data["source"]["date"] = "2027-01-01"
    assert respond(data).status == "refusal"


def test_demo_http_flow_and_web_assets():
    repository = KnowledgeRepository.load(ROOT / "examples")
    client = TestClient(create_app(repository, demo_mode=True))
    response = client.post("/api/v1/chat", json={"question": "测试借书"})
    assert response.status_code == 200
    assert response.json()["demo_mode"] is True
    assert response.json()["status"] == "card"
    assert client.get("/").status_code == 200
    assert client.get("/web/app.js").status_code == 200


def test_invalid_json_fails_instead_of_silent_partial_load(tmp_path):
    (tmp_path / "bad.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError):
        KnowledgeRepository.load(tmp_path)


def test_missing_optional_fields_are_explicit_unknowns():
    data = record()
    data["fields"]["location"] = None
    result = respond(data)
    assert result.status == "card"
    assert result.card.location.startswith("未查到明确信息")


def test_past_deadline_never_rewritten_to_future():
    data = record()
    data["fields"]["deadline"] = "2026-10-07"
    data["chunk_text"] += "截止日期：2026-10-07。"
    assert respond(data).status == "refusal"
    data["fields"]["deadline"] = "2026-10-08"
    data["chunk_text"] += "新版截止日期：2026-10-08。"
    assert respond(data).card.deadline == date(2026, 10, 8)


def test_duplicate_chunk_id_rejected(tmp_path):
    text = json.dumps(record(), ensure_ascii=False)
    (tmp_path / "one.json").write_text(text, encoding="utf-8")
    (tmp_path / "two.json").write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="知识片段标识重复"):
        KnowledgeRepository.load(tmp_path)
