# 本机环境检查（2026-10-08）

- Git 可用。
- Python 默认版本为 3.14，不符合后端要求；检测到另一项目工具目录中的 Python 3.11.16，可用于本地虚拟环境初始化。该目录不属于本项目发布依赖，其他成员需要自行安装 Python 3.11。
- Flutter 未找到，Android 平台工程和 APK 构建尚未验证。
- Docker 未找到，不影响本地后端开发。
- 已通过 Python 源文件 AST、JSON 和 pyproject.toml 语法检查。
- 已建立 `backend/.venv`，安装后端开发依赖；3 项接口测试、Ruff 静态检查和健康检查通过。
- 卡片 JSON Schema 从后端 ActionCard 模型生成，避免手写契约与模型不一致。
- 测试依赖存在 Starlette 对 httpx TestClient 的弃用提示，当前测试通过，后续升级时处理。

如果 `py -3.11` 无法选中安装的 3.11，使用 Python 3.11 可执行文件的完整路径执行 `-m venv backend/.venv`。不要改用默认 3.14。
