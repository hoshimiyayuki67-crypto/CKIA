"""RAG 链路基础测试。"""
from app.core import intent
from app.intelligence import rag
from app.schemas.card import Refusal


def test_refusal_returns_contact():
    """检索不到依据时应拒答，并给出咨询渠道。"""
    result = rag.refusal("资助")
    assert isinstance(result, Refusal)
    assert result.contact == "学生资助管理中心"


def test_intent_rewrite_expands_synonyms():
    """口语化提问应被改写为包含规范术语的查询。"""
    rewritten = intent.rewrite("那个钱怎么领")
    assert "资助" in rewritten
