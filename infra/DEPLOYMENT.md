# 当前部署记录

2026-10-08 已部署并从开发机通过公网验证。

- API：`https://v4.yukifn.xyz:7010`
- 健康检查：`https://v4.yukifn.xyz:7010/health`
- 服务器：ARM64 Armbian / Ubuntu 26.04。
- 源码目录：`/opt/campus-assistant`，使用 Git archive 上传已提交源码。
- 应用源码版本：`fbdcfb39d75cd7da9ee0fb9a3236da3e1e4c8037`。
- API 镜像：`campus-assistant-api:fbdcfb3`。
- Compose：`infra/compose.yaml` + `infra/compose.tls.yaml`，环境文件 `infra/.env`。
- 网关监听服务器 7010，转发至 API；API 只发布到 `127.0.0.1:8000`。
- Docker 服务启用开机启动，两个容器使用 `unless-stopped` 重启策略。

健康状态为 `ok`、`demo_mode=false`、`knowledge_status=not_configured`，`ai_status=configured`、`ai_model=deepseek-flash`。DeepSeek 官方模型列表验证通过，公网 `/api/v1/chat` 使用 `--require-ai` 验证真实模型调用成功、`ai_status=used`，无依据时仍拒答。当前无学校审核资料，不提供虚构办事依据。

模型密钥只保存在服务器权限 0600 的 `infra/.env`，由 Compose 注入后端容器。现有在线 APK 直接连接新版后端，无需重构建。调用限额及故障降级见 [后端开发](../backend/DEVELOPMENT.md)。本地 32 项后端测试和 Backend container 工作流均通过。

证书保存在服务器 `/etc/letsencrypt`，通过手动 DNS-01 验证签发，到期时间为 **2027-01-06 10:28:09 UTC**。本次没有 DNS API 凭据，续期需再次添加 DNS TXT 记录，不能依靠默认 certbot 定时器自动续期。续期完成后重新加载网关：

```bash
cd /opt/campus-assistant
certbot certonly --manual --preferred-challenges dns -d v4.yukifn.xyz
docker compose --env-file infra/.env -f infra/compose.yaml -f infra/compose.tls.yaml exec gateway caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
python3 scripts/check-backend-deployment.py https://v4.yukifn.xyz:7010
```

SSH 密码、证书私钥和部署 `.env` 不存入仓库。镜像采用 `.env.example` 中可配置的入口，本次使用 Amazon ECR Public。

Android 工作流 main 推送默认构建连接此 API 的在线 APK；PR 构建仍为离线演示，手动运行可选择演示模式或其他 HTTPS API。旧离线 APK 需要手动替换为新在线构建。
