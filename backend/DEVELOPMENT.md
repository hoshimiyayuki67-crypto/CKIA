# 后端开发

在项目根目录执行（Windows PowerShell，Python 3.11）：

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e '.[dev]'
.\.venv\Scripts\python.exe -m uvicorn campus_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器预览：`http://127.0.0.1:8000/`；接口说明：`http://127.0.0.1:8000/docs`；健康检查 `GET /health`。默认从项目 `knowledge/processed/` 加载 JSON 记录；没有审核通过的现行记录时拒答。该接口不存储请求、不调用模型。

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

结构校验不会执行人工审核或自动设置 reviewed。可用 `CAMPUS_KNOWLEDGE_DIR` 指定另一个资料目录；配置不存在的目录或坏记录将阻止启动。新增/更新 JSON 后重启服务。检索目前仅支持经过人工维护的事项别名，不进行资格推断；没有覆盖的问题会拒答，多条命中会要求澄清。向量混合检索、模型生成与自动抽取后续再集成。

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

后续模型密钥以 `.env.template` 为字段说明。服务不加载 .env 文件，当前仅读取明确设置的 CAMPUS_DEMO 和 CAMPUS_KNOWLEDGE_DIR 环境变量。

`requirements-dev.lock.txt` 记录首次验证环境的完整第三方包版本（无哈希，Windows/Python 3.11），不包含本项目和 pip/setuptools。变更依赖后重新安装验证并更新版本清单。
