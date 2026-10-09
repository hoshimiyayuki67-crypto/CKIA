# 后端开发

在项目根目录执行（Windows PowerShell，Python 3.11）：

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e '.[dev]'
.\.venv\Scripts\python.exe -m uvicorn campus_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器预览：`http://127.0.0.1:8000/`；接口说明：`http://127.0.0.1:8000/docs`；健康检查 `GET /health`。默认从项目 `knowledge/processed/` 加载 JSON 记录；没有审核通过的现行记录时拒答。接口不存储请求；设置 `DEEPSEEK_API_KEY` 后向 DeepSeek 发送用户问题与最多八条合格资料用于语义匹配。

## 演示问答与卡片

在 backend 目录运行：

```powershell
$env:CAMPUS_DEMO = '1'
.\.venv\Scripts\python.exe -m uvicorn campus_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

打开浏览器预览，输入“测试馆借阅需要什么材料？”。演示模式仅加载 `examples/` 的虚构记录，并在页面和响应中明确标识。可勾选材料、查看出处元数据；测试出处没有真实 URL。勾选状态仅保存在当前页面，未接入离线缓存。

关闭服务并执行 `Remove-Item Env:CAMPUS_DEMO -ErrorAction SilentlyContinue` 后重新启动，即恢复默认模式。不要在实际使用环境开启演示模式。

## 接入真实资料

先依据 `contracts/knowledge-entry.schema.json` 人工整理原文和卡片字段，核验版本、日期和出处，未审核资料用 reviewed=false。来源片段中的日期需规范为 ISO 格式，同时保留原文件供核对。片段必须包含卡片所引用的原文表述，空缺字段使用 null。

```powershell
.\.venv\Scripts\python.exe -m campus_assistant.repositories.validate ../knowledge/processed
```

结构校验不会执行人工审核或自动设置 reviewed。可用 `CAMPUS_KNOWLEDGE_DIR` 指定另一个资料目录；不存在的目录或坏记录会阻止启动。资料更新后重启服务。未配置模型时按事项别名检索，配置 DeepSeek 后支持语义匹配，不进行资格推断。无相关资料时拒答，多条命中要求澄清。向量混合检索、自由文本生成和自动抽取仍待接入。

另开终端验证：

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

可选浏览器验证（Windows 已安装 Edge）：

```powershell
.\.venv\Scripts\python.exe scripts/smoke_web.py
```

脚本自动启动本地演示服务并在验证结束后关闭，检查卡片、材料勾选、类别拒答和用户输入作为文字渲染；验证页面和日志输出到忽略提交的 artifacts/。

模型配置见 `.env.template`。服务不自动加载 .env 文件，本地应设置环境变量；Docker Compose 使用服务器 `infra/.env` 注入。

## DeepSeek 接入

设置 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL=https://api.deepseek.com`、`DEEPSEEK_MODEL=deepseek-flash` 并重启。密钥只配置后端，不能提交仓库或进入 APK。健康检查 `ai_status=configured` 仅表示已配置；实际响应 `ai_status=used` 才表示模型调用成功，故障时为 `unavailable`，未启用为 `disabled`。

模型返回受限 JSON，只选择真实片段编号或识别问候；字段、出处和用户可见文本由后端依据审核记录生成。非法编号、额外生成字段及截断输出会降级。没有资料时仍能理解问题，但不会生成学校规定。此阶段不是开放域聊天或完整向量 RAG。

候选上限八条，每条正文最多 1500 字，别名优先；扩大资料覆盖时需接入向量召回。单 worker 每 IP 每分钟六次、全局每分钟三十次、最多两次并发调用。HTTP 和总调用时间受限制，无自动重试。多 worker 部署前需迁移至共享限流。请求正文、密钥和供应商错误正文不写入日志。

参考：[DeepSeek Chat Completions](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)。

## 院校与联网证据

v0.5 增加官网正文/内部页面检索、带原文支撑的归纳总结与 SQLite 账号/云端聊天，接口、存储和验证详见 [v0.5](../development/v0.5.md)。开发时可设置 `CAMPUS_DATA_DIR` 指向工作区内的临时目录启用账号；生产使用持久命名卷。

`school_id` 默认 imuchuangye；本地审核知识按院校隔离。`search_enabled` 默认 false，不调用搜索服务。联网查询使用服务器 `TAVILY_API_KEY`，只请求所选院校官网域名，并与审核记录共同交给模型筛选可验证原文证据；网络摘要不能生成正式办事卡片。未配置密钥、网络错误或非法模型分析都明确降级。配置、接口字段和客户端使用详见 [v0.4](../development/v0.4.md)。

`requirements-dev.lock.txt` 记录首次验证环境的完整第三方包版本（无哈希，Windows/Python 3.11），不包含本项目和 pip/setuptools。变更依赖后重新安装验证并更新版本清单。
