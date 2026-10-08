# 后端开发

在项目根目录执行（Windows PowerShell，Python 3.11）：

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e '.[dev]'
.\.venv\Scripts\python.exe -m uvicorn campus_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

接口说明：`http://127.0.0.1:8000/docs`；健康检查 `GET /health`。`POST /api/v1/chat` 当前始终返回 `refusal`，明确说明知识库尚未接入，不生成假材料、期限或出处。该接口不存储请求、不调用模型。

另开终端验证：

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

后续密钥配置以 `.env.template` 为字段说明。目前骨架不加载该文件；集成提供方时需明确配置读取、校验和失败行为。智能层/数据层目录目前只有职责说明。

`requirements-dev.lock.txt` 记录首次验证环境的完整第三方包版本（无哈希，Windows/Python 3.11），不包含本项目和 pip/setuptools。变更依赖后重新安装验证并更新版本清单。
