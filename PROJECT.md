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

交付目标为 Android APK，由 GitHub Actions 构建；操作见 mobile/DEVELOPMENT.md。Flutter 已实现原生对话、类别筛选、卡片、本地记录与勾选保存、资料夹、院校选择、联网开关、拍照识别、本地提醒和离线资料查看；详见 [v0.4](development/v0.4.md)。

后端已接入 DeepSeek 与 Tavily，支持院校官网深度检索、可读总结和支撑原文，并提供账号及云端聊天同步。v1.0.0 加入最近12条对话上下文、教育部名单中的1412所本科院校检索、2021年9月学生手册参考库、新图标和系统/手动暗黑模式，详见 [正式版验收](development/v1.0.md)。每日加密备份、异地恢复与固定签名已验证。HTTPS自动续期按用户要求取消，使用手动DNS续期。正式审核办事卡片资料仍为空，向量混合检索与云端推送未实现。H5 为辅助预览。

仓库中原有 `app/`、`android/` 等文件处于删除状态，本次未恢复；新代码放入独立目录，便于审阅迁移。设计文档保持原样。
