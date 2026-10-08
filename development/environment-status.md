# 本机环境检查（2026-10-08）

- Git 可用。
- Python 默认版本为 3.14，不符合后端要求；检测到另一项目工具目录中的 Python 3.11.16，可用于本地虚拟环境初始化。该目录不属于本项目发布依赖，其他成员需要自行安装 Python 3.11。
- Flutter 未找到，Android 平台工程和 APK 构建尚未验证。
- Docker 未找到，不影响本地后端开发。
- 已通过 Python 源文件 AST、JSON 和 pyproject.toml 语法检查。
- 已建立 `backend/.venv`，安装后端开发依赖；3 项接口测试、Ruff 静态检查和健康检查通过。
- 卡片 JSON Schema 从后端 ActionCard 模型生成，避免手写契约与模型不一致。
- 测试依赖存在 Starlette 对 httpx TestClient 的弃用提示，当前测试通过，后续升级时处理。

## 首轮功能验证

- 16 项后端测试通过，覆盖卡片来源绑定、拒答、澄清、审核状态、分类、日期、字段校验和重复片段。
- 使用本机 Edge 无界面模式验证 H5 卡片、材料勾选、类别拒答和文字安全渲染，未出现页面脚本错误。
- 可执行 scripts/start-dev.ps1 -Demo 查看虚构测试数据；真实资料、LLM、Flutter 和推送尚未接入。

如果 `py -3.11` 无法选中安装的 3.11，使用 Python 3.11 可执行文件的完整路径执行 `-m venv backend/.venv`。不要改用默认 3.14。
