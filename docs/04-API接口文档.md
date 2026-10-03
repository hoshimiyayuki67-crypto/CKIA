# 04 API 接口文档

> 服务基地址：`http://<host>:8000`　接口文档（Swagger）：`/docs`
> 后端同时服务两类客户端：**安卓 APP（JSON）** 与 **微信公众号/企业微信（XML）**，
> 二者共用 `app.core.agent.process` 处理链路，仅输出形式不同。

## 一、接口总览

| 方法 | 路径 | 说明 | 客户端 |
| --- | --- | --- | --- |
| POST | `/api/v1/chat` | 文字提问 | 安卓 |
| POST | `/api/v1/chat/image` | 截图提问（以图问图） | 安卓 |
| POST | `/api/v1/feedback` | 回答反馈（有用/没用） | 安卓 |
| GET | `/wechat` | 微信服务器 URL 校验 | 微信 |
| POST | `/wechat` | 接收用户消息并返回回复 | 微信 |
| GET | `/health` | 健康检查 | 通用 |

统一响应信封（安卓接口）：

```json
{ "type": "card | refusal | text", "data": { ... } }
```

---

## 二、安卓端 JSON 接口

对应代码：[app/api/chat.py](../app/api/chat.py)、[app/schemas/api.py](../app/schemas/api.py)。

### 1. POST /api/v1/chat —— 文字提问

**请求体（application/json）**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| session_id | string | 是 | 匿名会话标识（APP 端 UUID，不采集个人信息） |
| question | string | 是 | 学生提问文本 |

```json
{ "session_id": "8f3c...", "question": "助学贷款怎么申请？" }
```

**响应体**

```json
{
  "type": "card",
  "data": {
    "matter_name": "生源地信用助学贷款 · 首次申请",
    "target_users": ["在校本专科生"],
    "materials": [
      { "item": "录取通知书原件及复印件", "required": true, "note": null }
    ],
    "location": "学生资助管理中心 3号窗口",
    "office_hours": "周一至周五 9:00–17:00",
    "deadline": "2026-10-20",
    "channel": "线下",
    "contact": "学生资助管理中心",
    "sources": [
      { "title": "关于做好2026年生源地信用助学贷款工作的通知", "issuer": "学生工作处", "date": "2026-10-08" }
    ],
    "notes": [],
    "confidence": 0.9
  }
}
```

拒答时：

```json
{
  "type": "refusal",
  "data": {
    "intent": "资助",
    "message": "未查询到相关规定，建议咨询学生资助管理中心。",
    "contact": "学生资助管理中心"
  }
}
```

澄清追问 / 版本差异 / 降级文本时：

```json
{ "type": "text", "data": { "text": "你是想了解首次申请还是续贷？" } }
```

### 2. POST /api/v1/chat/image —— 截图提问（以图问图）

**请求体（multipart/form-data）**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| session_id | string | 是 | 匿名会话标识 |
| question | string | 否 | 附加问题，如「这个我能报吗」 |
| file | file | 是 | 通知截图文件 |

**响应体**：同 `/api/v1/chat`（统一信封）。

### 3. POST /api/v1/feedback —— 回答反馈

**请求体**

```json
{ "message_id": "a1b2...", "useful": true }
```

**响应体**

```json
{ "ok": true }
```

### 4. GET /health —— 健康检查

```json
{ "status": "ok", "service": "campus-agent", "version": "0.1.0" }
```

---

## 三、微信端 XML 接口

### 1. GET /wechat —— 服务器校验

微信公众平台配置服务器地址时用于回显 `echostr`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| signature | string | 是 | 微信加密签名 |
| timestamp | string | 是 | 时间戳 |
| nonce | string | 是 | 随机数 |
| echostr | string | 是 | 校验通过后原样返回 |

- 通过：`200`，`text/plain`，body 为 `echostr`；
- 失败：`403`，body 为 `invalid signature`。

**签名算法**：将 `token`、`timestamp`、`nonce` 字典序排序后拼接，做 SHA1 摘要，与 `signature` 比对。

### 2. POST /wechat —— 接收用户消息

**请求体（XML，微信定义）**

```xml
<xml>
  <ToUserName><![CDATA[公众号原始ID]]></ToUserName>
  <FromUserName><![CDATA[用户OpenID]]></FromUserName>
  <CreateTime>1730000000</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[助学贷款怎么申请？]]></Content>
</xml>
```

图片消息通过 `MsgType=image` 与 `PicUrl` 传递（对应 [app/utils/wechat_xml.py](../app/utils/wechat_xml.py)）。

**响应体（XML）**

```xml
<xml>
  <ToUserName><![CDATA[用户OpenID]]></ToUserName>
  <FromUserName><![CDATA[campus-agent]]></FromUserName>
  <CreateTime>1730000001</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[📋 生源地信用助学贷款 · 首次申请
─────────────────────
…]]></Content>
</xml>
```

> 微信端卡片由 [app/render/card_wechat.py](../app/render/card_wechat.py) 渲染为文本；安卓端则由 Compose 组件 `ActionCardView` 渲染为可勾选的原生卡片。

---

## 四、内部处理约定

以下为服务内部流程，不对外暴露，供开发与联调参考。

| 环节 | 入口 | 输入 → 输出 |
| --- | --- | --- |
| 处理链路（两客户端共用） | `app.core.agent.process` | `session_hash, question, image` → `ActionCard \| Refusal \| str` |
| RAG 主链路 | `app.intelligence.rag.answer` | `question, image` → `ActionCard \| Refusal \| str` |
| 意图识别 | `app.core.intent.classify` | `question` → `Intent` |
| 查询改写 | `app.core.intent.rewrite` | `question` → `str` |
| 混合检索 | `app.intelligence.retriever.hybrid_search` | `query, category` → `RetrievedChunk[]` |
| 字段抽取 | `app.core.extractor.extract` | `draft` → `dict` |
| 卡片组装 | `app.core.card.build_card` | `fields, sources` → `ActionCard` |

---

## 五、错误与降级

| 场景 | 行为 |
| --- | --- |
| 检索相关度低于阈值 | 返回拒答说明 + 咨询渠道（`type=refusal`） |
| 模型生成 / JSON 解析失败 | 降级为带出处的纯文本答案（`type=text`） |
| 截图识别置信度低 | 提示「图片较模糊，建议重新上传或直接描述问题」 |
| 截图与正式文件不一致 | 主动提示差异，并以官方文件为准 |
| 网络异常（安卓端） | APP 侧展示「网络异常，请稍后重试」，已发送消息保留在会话中 |
| 服务异常 | 不使用"服务异常，请稍后再试"，保证至少返回兜底话术与咨询出路 |
