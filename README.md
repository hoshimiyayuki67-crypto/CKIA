# 校园万事通

> 装进手机里的校园事务智能体 —— 学生用一句话、或者一张通知截图提问，即可获得一份可照着办的办事清单。

| 项 | 内容 |
| --- | --- |
| 参赛赛道 | 赛道一（大模型与智能体） |
| 项目负责人 | 张紫涵 |
| 所在学校 | 内蒙古大学创业学院 |
| 交付形态 | **安卓 APK**（Kotlin + Jetpack Compose），另有微信公众号 / 企业微信入口 |
| 技术底座 | 大语言模型 + 检索增强生成（RAG）+ 多模态理解 |

## 一句话定义

校园万事通是一个校园事务智能体：学生用一句话、或者一张通知截图提问，即可获得一份可照着办的办事清单。

## 核心创意

把「信息检索」改造成「事务代办」：回答不是终点，「能办成事」才是。

- **宁可说"不知道"，绝不编造** —— 检索不到依据时明确拒答并给出咨询渠道；
- **每个答案都能追到源头** —— 强制标注文件名、发布部门、发布日期；
- **输出必须能直接用** —— 结构化办事卡片（材料清单可勾选、地点到窗口、时间到时段）；
- **主动，而不是等待询问** —— 关键节点由系统跟着学期日历主动推送。

## 覆盖范围

覆盖 **资助、教务、财务、学籍、就业、生活** 六大类校园事务，首批实现不少于 15 类高频事项的智能应答。

## 系统架构

```
┌───────────────────────────┐   ┌───────────────────────────┐
│ 安卓 APP（Kotlin+Compose）│   │ 微信公众号 / 企业微信      │
│  聊天界面 · 办事卡片 · 勾选│   │  XML 消息接入              │
└─────────────┬─────────────┘   └─────────────┬─────────────┘
              │ JSON REST (retrofit)          │ XML
              └───────────────┬───────────────┘
                              ▼
┌────────────────────────────────────────────────────────────┐
│ 后端（Python 3.11 + FastAPI）—— app/                        │
│  接入层 api/ · 应用层 core/ · 智能层 intelligence/ · 数据层 data/ │
│  RAG 检索增强 · 多模态截图理解 · 结构化办事卡片 · 主动提醒    │
└────────────────────────────────────────────────────────────┘
```

- **安卓 APP** 负责交互与呈现（聊天、办事卡片勾选、截图上传）；
- **后端** 负责检索、生成、字段抽取与调度（所有模型调用与服务端逻辑）；
- 微信端与安卓端**共用同一条处理链路** `app.core.agent.process`，仅输出形式不同（XML / JSON）。

## 技术栈

### 安卓客户端

| 类别 | 方案 |
| --- | --- |
| 语言 / UI | Kotlin + Jetpack Compose（Material 3） |
| 架构 | MVVM（ViewModel + Compose State） |
| 网络 | Retrofit + OkHttp + Gson |
| 图片 | Coil（截图预览） |
| 构建 | Gradle 8.9 / AGP 8.7 / Kotlin 2.0（minSdk 24、targetSdk 35） |

### 后端服务

| 类别 | 方案 |
| --- | --- |
| 框架 | Python 3.11 + FastAPI |
| 大语言模型 | DeepSeek / 通义千问 API |
| 嵌入 / 重排 | BGE 系列中文模型 |
| 向量库 | Chroma（开发）/ Milvus（生产） |
| 视觉模型 | Qwen-VL / GLM-4V |
| 调度 | APScheduler |
| 文档解析 | PyMuPDF + python-docx |
| 部署 | Docker + 云服务器 |

## 目录结构

```
校园万事通/
├── app/                      # 后端（四层架构）
│   ├── main.py               # FastAPI 入口
│   ├── config.py
│   ├── api/                  # 接入层：chat.py（安卓 JSON）/ wechat.py（微信 XML）
│   ├── core/                 # 应用层：agent 编排 + 会话/意图/多模态/抽取/卡片/调度/反馈/分析
│   ├── intelligence/         # 智能层：LLM/嵌入/重排/视觉/RAG
│   ├── data/                 # 数据层：向量库/文档库/知识库原始文档
│   ├── render/               # 微信端卡片渲染
│   ├── schemas/              # 数据结构（含安卓 API 信封）
│   └── utils/
├── android/                  # 安卓工程（Kotlin + Compose）
│   ├── settings.gradle.kts / build.gradle.kts / gradle.properties
│   └── app/
│       ├── build.gradle.kts          # 依赖与 API_BASE_URL 配置
│       └── src/main/
│           ├── AndroidManifest.xml
│           ├── res/                  # 字符串/主题/图标/网络安全配置
│           └── java/com/campus/wanshitong/
│               ├── MainActivity.kt / CampusApplication.kt
│               ├── data/             # dto / api / remote / local / repository / model
│               └── ui/               # theme / chat（ChatScreen、组件）
├── config/timeline.yaml      # 学期时间轴
├── docs/                     # 项目开发文档
├── scripts/                  # 知识库入库、金标测试
├── tests/                    # 测试与金标测试集
├── requirements.txt / .env.example / Dockerfile / docker-compose.yml
```

## 快速开始

### 1. 启动后端

```bash
pip install -r requirements.txt
copy .env.example .env        # Windows；Linux/macOS 用 cp
uvicorn app.main:app --reload --port 8000
# 接口文档：http://localhost:8000/docs
```

### 2. 运行安卓 APP

**方式一：仓库内 CI 自动构建（推荐）** —— 推送到 `main` 后由 Gitea Actions 自动出包，
在仓库 Actions 页面 → Artifacts 下载 `app-debug-apk`。工作流见 [.gitea/workflows/android.yml](.gitea/workflows/android.yml)。

**方式二：本地构建**

```bash
cd android
./gradlew assembleDebug        # 产物：app/build/outputs/apk/debug/app-debug.apk
# 或 Android Studio 打开 android/ 直接运行
```

- **模拟器**：默认 `API_BASE_URL = http://10.0.2.2:8000/`（指向宿主机），可直接用；
- **真机**：把 [app/build.gradle.kts](android/app/build.gradle.kts) 的 `API_BASE_URL` 改为电脑局域网 IP，
  并把该 IP 加入 [network_security_config.xml](android/app/src/main/res/xml/network_security_config.xml) 的明文白名单。

> 首次运行需要本地已生成 Gradle Wrapper（`gradle wrapper`）；仓库仅包含 `gradle-wrapper.properties`。也可用 Android Studio 打开 `android/` 让其自动补全。

### 3. 微信端（可选）

`POST /wechat` 接收微信服务器 XML 推送，配置 `WECHAT_*` 环境变量后即可接入。

## 文档索引

| 文档 | 说明 |
| --- | --- |
| [01-需求说明](docs/01-需求说明.md) | 项目背景、场景、功能范围与优先级 |
| [02-技术架构设计](docs/02-技术架构设计.md) | 客户端 + 后端架构、技术选型、RAG 与多模态方案 |
| [03-数据结构设计](docs/03-数据结构设计.md) | 知识库条目、办事卡片、会话日志结构 |
| [04-API接口文档](docs/04-API接口文档.md) | 安卓 JSON 接口 + 微信 XML 接口 |
| [05-提示词设计](docs/05-提示词设计.md) | 系统提示词与字段校验规则 |
| [06-开发计划与环境](docs/06-开发计划与环境.md) | 开发阶段、里程碑、环境与运行 |
| [07-测试与验收方案](docs/07-测试与验收方案.md) | 测试指标体系、方法与验收标准 |

## 设计原则（工程约束）

1. 检索不到依据时**必须拒答**，不允许模型自由发挥；
2. 所有回答**强制标注出处**；
3. 卡片字段抽不到时统一填「未查到明确信息」，**绝不自行填充**；
4. 官方层与经验层冲突时，**以官方层为准**并主动提示；
5. 任一环节失败时，保证至少输出**带出处的纯文本答案**，不出现空手而归。

> 完整创意与设计说明见 [校园万事通_软件创意设计文档.md](校园万事通_软件创意设计文档.md)。
