# 跨端契约

当前可调用：`GET /health`、`POST /api/v1/chat`。后端运行时 `/openapi.json` 为接口契约；action-card.schema.json、chat-response.schema.json 和 knowledge-entry.schema.json 均由 Pydantic 模型生成。

提问示例：`{"question":"助学贷款需要什么材料？","category":"资助"}`，category 可省略。空白问题、超过 2000 字或额外字段返回 422。

回答状态：card（审核资料中的卡片）、refusal（无有效依据）、clarification（多个事项命中）。仅 card 状态携带 card 和与卡片一致的 sources；其余状态 card=null、sources=[]。ai_generated=true 表示 AI 助手输出标识，当前使用确定性整理，未调用大模型。demo_mode 标明是否仅使用虚构演示资料。

Source 比设计文档增加 doc_id、chunk_id、可选 url，用于实际来源绑定和跳转。deadline 为 ISO 日期或 null；unknown 信息不伪造日期。materials.required 表示官方要求，用户勾选状态属于本地记录。

confidence 目前固定为 0.6，是初版保守占位值，不表示模型测量结果或资格判断正确率。不要据此做办理资格决策。

修改模型后，在 backend 目录运行 `.\.venv\Scripts\python.exe scripts/export_contracts.py`，将生成的契约与模型一同评审。
