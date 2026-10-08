# 跨端契约

当前可调用：`GET /health`、`POST /api/v1/chat`。后端运行时 `/openapi.json` 为现有接口契约；`action-card.schema.json` 为待实现卡片结构，不表示 chat 已支持卡片成功响应。

提问示例：`{"question":"助学贷款需要什么材料？","category":"资助"}`，category 可省略。空白问题、超过 2000 字或额外字段返回 422。

当前回答：status 为 refusal，card 为 null，sources 为空，ai_generated 为 true。实现检索之后再新增 card/text/clarification 状态并同步端侧解析，不能直接改变现有语义。

Source 比设计文档增加 doc_id、chunk_id、可选 url，用于实际来源绑定和跳转。deadline 为 ISO 日期或 null；unknown 信息不伪造日期。materials.required 表示官方要求，用户勾选状态属于本地记录。
