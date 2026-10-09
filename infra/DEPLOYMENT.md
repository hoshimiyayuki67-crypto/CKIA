# 当前部署记录

2026-10-09 已更新正式版后端并从开发机通过公网验证。

- API：`https://v4.yukifn.xyz:7010`
- 健康检查：`https://v4.yukifn.xyz:7010/health`
- 服务器：ARM64 Armbian / Ubuntu 26.04。
- 源码目录：`/opt/campus-assistant`，使用 Git archive 上传已提交源码。
- 应用运行源码版本：`c352dd5`（v1.0.0 后端）。
- API 镜像：`campus-assistant-api:c352dd5`。
- Compose：`infra/compose.yaml` + `infra/compose.tls.yaml`，环境文件 `infra/.env`。
- 网关监听服务器 7010，转发至 API；API 只发布到 `127.0.0.1:8000`。
- Docker 服务启用开机启动，两个容器使用 `unless-stopped` 重启策略。

健康状态为 `ok`、`demo_mode=false`、`knowledge_status=loaded`、`document_chunks=73`，`ai_status=configured`、`ai_model=deepseek-flash`、`search_status=configured`。手册为2021年9月历史参考版本；已审核的现行办事卡片资料仍为空。真实模型手册总结、上下文追问、跨院校隔离、浙江大学官网精准搜索与摘要已验证。无已知官网的登记院校云端聊天保存/读取也已通过临时账号验证，测试账号已删除。

模型密钥只保存在服务器权限 0600 的 `infra/.env`，由 Compose 注入后端容器。现有在线 APK 直接连接新版后端；v0.5 归纳总结、来源折叠、账号等新入口需要新版 APK。调用限额及故障降级见 [后端开发](../backend/DEVELOPMENT.md)。本地48项后端测试通过；Android Actions 完成静态分析、12项 Flutter 测试和 APK 构建。

v0.5 账号数据库使用 `campus-assistant_campus-data` 命名卷；`accounts_status=configured`。已通过公网创建随机临时账号、保存与读取聊天、另一账号隔离和删除账号验证；验证后立即删除临时账号与对话，不留下凭据文件。数据库重启持久性、版本冲突、删除标记与配额由后端回归覆盖。手机令牌使用安全存储，服务器仅保存密码与令牌摘要。账号、同步和数据维护见 [v0.5](../development/v0.5.md)。

`6f8d542` 公网真实检索验证：北京大学在校生/毕业生成绩单问题返回6份官网正文，并生成办理步骤、所需材料、时间与地点、注意事项4段归纳总结，`search_status=used`、`ai_status=used`。模型支撑引文的换行/Markdown/标点差异会映射回实际原文；伪造文字或变更金额仍拒绝。v0.5.0 APK 已由 Android APK 工作流成功构建并上传 Release，发布步骤校验了文件 SHA256。

2026-10-09 已将 Tavily 密钥保存到服务器权限 0600 的环境文件并重建容器配置，健康检查为 `search_provider=tavily`、`search_status=configured`。真实搜索验证：创业学院奖学金问题返回2条官网结果；公网北京大学成绩单问题返回5条官网结果和6条经原文校验的 DeepSeek 引用证据，`search_status=used`、`ai_status=used`。关闭开关时为 `search_status=disabled`、无联网结果。学校正式审核知识库仍为空；网络摘要不得生成正式办理卡片。院校接口、缺失密钥降级，以及隔离测试资料 + 模拟搜索摘要 + 真实 DeepSeek 的混合证据分析也已验证。配置步骤见 [v0.4](../development/v0.4.md)。

使用隔离演示记录对真实模型执行完整匹配与卡片校验，结果为 `status=card`、`ai_status=used`，来源与卡片绑定一致。该验证不向正式知识目录写入演示资料。模型引用采用文件编号与片段编号生成的固定引用键，避免模型拆分复合编号。

证书保存在服务器 `/etc/letsencrypt`，通过手动 DNS-01 验证签发，到期时间为 **2027-01-06 10:28:09 UTC**。本次没有 DNS API 凭据，续期需再次添加 DNS TXT 记录，不能依靠默认 certbot 定时器自动续期。续期完成后重新加载网关：

```bash
cd /opt/campus-assistant
certbot certonly --manual --preferred-challenges dns -d v4.yukifn.xyz
docker compose --env-file infra/.env -f infra/compose.yaml -f infra/compose.tls.yaml exec gateway caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
python3 scripts/check-backend-deployment.py https://v4.yukifn.xyz:7010
```

SSH 密码、证书私钥和部署 `.env` 不存入仓库。镜像采用 `.env.example` 中可配置的入口，本次使用 Amazon ECR Public。

2026-10-09 已启用 ckia-backup.timer（北京时间02:30），保留7份服务器加密快照；GitHub 每日02:45导出并保留30天。首次异地恢复与密文篡改拒绝验证通过，正式版部署后备份执行成功，详见 [恢复说明](maintenance/README.md)。HTTPS自动续期按用户要求取消，不再等待Cloudflare Token，保留手动DNS续期方式。

Android 工作流 main 推送默认构建连接此 API 的在线 APK；PR 构建仍为离线演示，手动运行可选择演示模式或其他 HTTPS API。旧离线 APK 需要手动替换为新在线构建。
