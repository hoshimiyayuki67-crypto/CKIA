# 后端服务器部署

默认模式不加载虚构资料；没有审核资料时，API 可以正常运行并明确拒答。尚未接入大模型，本次部署不需要模型密钥。当前是开发服务，不代表真实学校事务已覆盖。

## 服务器前提

Linux + Docker Engine + Docker Compose v2。部署前检查现有容器、端口、网站和防火墙；已有网关时复用，不占用已有 80/443 服务。

## 启动后端

在服务器用户自己的目录中克隆仓库，或通过 git archive 上传当前提交的源码：

```bash
git clone https://github.com/hoshimiyayuki67-crypto/CKIA.git campus-assistant
cd campus-assistant
mkdir -p knowledge/processed
docker compose -f infra/compose.yaml config --quiet
docker compose -f infra/compose.yaml up -d --build --wait --wait-timeout 120
docker compose -f infra/compose.yaml ps
python3 scripts/check-backend-deployment.py http://127.0.0.1:8000
```

API 默认只绑定服务器 127.0.0.1:8000，由现有 HTTPS 网关或下述可选网关对外提供访问。应用容器使用非 root 用户、只读文件系统、只读资料挂载、健康检查、日志轮转和退出重启。健康检查失败本身不会自动重启仍在运行的进程，应排查日志。

## HTTPS 入口

若服务器已有 Nginx/Caddy/面板反向代理，将 HTTPS 域名根路径转发到 http://127.0.0.1:8000，保留 /api/v1 和 /health 路径。容器中的既有网关需要配置适合其网络的上游地址，不能使用该网关容器自己的 127.0.0.1。

没有网关时，可使用 compose.https.yaml 中的 Caddy：

```bash
cp infra/.env.example infra/.env
# 编辑 infra/.env：CAMPUS_DOMAIN=api.example.com，不包含 https:// 和路径
docker compose --env-file infra/.env -f infra/compose.yaml -f infra/compose.https.yaml config --quiet
docker compose --env-file infra/.env -f infra/compose.yaml -f infra/compose.https.yaml up -d --build --wait --wait-timeout 120
python3 scripts/check-backend-deployment.py https://api.example.com
```

域名 A/AAAA 需指向服务器，80/443 TCP 需可访问；Caddy 会申请并续期公开证书。证书状态保存在 caddy_data 卷中，保留该卷。不要为排查证书问题执行 down -v。没有可信 HTTPS 域名前，当前 release APK 不能连接该服务器，只能通过 SSH 转发调试后端。

参考：[Caddy 自动 HTTPS](https://caddyserver.com/docs/automatic-https)、[Compose 健康启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)。

## 资料与更新

把审核过的 JSON 记录放在 knowledge/processed，确保容器 UID 10001 能读取目录和文件。该目录只读挂载且不会被打包入镜像。先验证记录，再重启 API：

```bash
docker compose -f infra/compose.yaml exec api python -m campus_assistant.repositories.validate /app/knowledge/processed
docker compose -f infra/compose.yaml restart api
```

更新之前记下当前 Git 提交和镜像 ID，并备份资料。拉取更新后重建；使用网关的部署始终带相同的 env-file 和两份 Compose 文件。建议每次设 CAMPUS_IMAGE_TAG 为提交 SHA，保留上一个镜像，以便回滚。当前没有数据库迁移，不会自动删除资料。

日志命令：`docker compose -f infra/compose.yaml logs --tail 100 api`。正常检查使用 /health；不记录请求正文，不把原始问题或截图放入日志。

## Android 连接

部署后验证 HTTPS /health 和 /api/v1/chat，再到 Android APK 的 Run workflow 设置 demo_mode=false，api_base_url=https://你的域名。已下载的离线演示 APK 不会自动切换为在线模式，需要下载这次在线构建的安装包。

## 验证状态

本机没有 Docker；容器构建及运行由 Backend container 工作流在 Linux 上验证。该工作流不部署到服务器，只运行后端测试、Compose 校验、镜像启动与 API 冒烟检查。服务器实际部署仍需 SSH 地址、用户名和域名信息。

调度服务与 Web worker 分离，提醒任务需要幂等键和持久化发送状态，避免多 worker 重复推送。开发 Chroma/生产 Milvus 的迁移需重新建立索引并运行同一金标集。
