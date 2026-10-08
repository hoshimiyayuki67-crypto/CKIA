# 校园万事通：开发入口

需求依据：[软件创意设计文档](校园万事通_软件创意设计文档.md)。交付目标是 Android APK，采用 Flutter + H5，后端为 Python 3.11 + FastAPI。

## 项目目录

```text
backend/                   Python 服务，可独立启动
  src/campus_assistant/
    api/                   HTTP 接口
    schemas/               请求、卡片与出处模型
    services/              会话、卡片、提醒等应用服务
    intelligence/          检索、生成、嵌入、重排、视觉适配
    repositories/          文档、索引、订阅存储适配
  tests/                   后端接口与安全行为测试
mobile/                    Flutter 客户端
  lib/features/            对话、卡片、提醒功能
  lib/core/                API、缓存、原生桥接
web/                       WebView H5 页面与桥接协议
contracts/                 跨端 JSON Schema 与协议说明
knowledge/                 官方/经验原文、处理后片段、收录清单
evaluation/                金标问答与评测报告
config/                    学期时间轴等非敏感配置
infra/                     容器与网关部署准备
scripts/                   开发环境检查
development/               架构、流程、任务清单
```

## 开始开发

1. 阅读 [开发流程](development/workflow.md) 和 [实现任务](development/backlog.md)。
2. 在项目根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/check-environment.ps1`。
3. 按后端、客户端各自说明安装依赖、启动与验证。

当前提供的是开发骨架：后端健康检查与安全拒答接口、Flutter 入口和 H5 占位页。尚未连接模型、知识库、推送或校内数据；不能用于实际办事判断。

仓库中原有 `app/`、`android/` 等文件处于删除状态，本次未恢复；新代码放入独立目录，便于审阅迁移。设计文档保持原样。
