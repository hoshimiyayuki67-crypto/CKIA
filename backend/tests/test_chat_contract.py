from fastapi.testclient import TestClient

from campus_assistant.main import create_app

client = TestClient(create_app())


def test_no_knowledge_cannot_invent_card_or_sources():
    response = client.post("/api/v1/chat", json={"question": "助学贷款需要什么材料？"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refusal"
    assert data["card"] is None
    assert data["sources"] == []
    assert data["ai_generated"] is True


def test_blank_question_rejected():
    response = client.post("/api/v1/chat", json={"question": "   "})
    assert response.status_code == 422


def test_unknown_fields_rejected():
    response = client.post(
        "/api/v1/chat", json={"question": "如何报销？", "student_id": "123"}
    )
    assert response.status_code == 422
