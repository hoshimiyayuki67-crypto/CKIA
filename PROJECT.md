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

已安装后端依赖时，可从根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/start-dev.ps1 -Demo`，访问 http://127.0.0.1:8000/ 演示卡片。省略 -Demo 使用正式资料目录，没有已审核资料时拒答。

交付目标为 Android APK，由 GitHub Actions 构建；操作见 mobile/DEVELOPMENT.md。Flutter 已实现原生对话、类别筛选、卡片和材料勾选，可离线演示或连接 HTTPS 后端。

后端已实现人工结构化知识记录加载、事项别名检索、来源与字段校验、卡片/拒答/澄清响应。H5 为辅助开发预览。正式模式尚无审核通过的学校资料，不用于实际办事判断；模型混合检索、真机验收、截图和推送仍待开发。

仓库中原有 `app/`、`android/` 等文件处于删除状态，本次未恢复；新代码放入独立目录，便于审阅迁移。设计文档保持原样。
