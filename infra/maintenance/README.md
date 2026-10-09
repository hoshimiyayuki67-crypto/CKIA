# 运维与恢复

服务器 ckia-backup.timer 每天北京时间02:30运行，保留最近7份加密备份。
GitHub Encrypted cloud backup 工作流02:45导出最新备份，Artifact保留30天。
专用SSH账号强制运行export_backup.py，不能执行任意命令。
备份使用RSA-OAEP封装随机AES-256-GCM密钥，包含SQLite在线快照、部署配置和证书。

恢复私钥及密码只保存在本机 artifacts/ops-private 受限目录，不提交仓库。
请将该目录安全备份到离线介质；遗失恢复密钥后无法解密备份。
固定签名密钥同时配置于GitHub Secret CKIA_CI_BUNDLE，不应重新生成。

隔离恢复（安装cryptography后运行）：

```powershell
python infra/maintenance/restore_backup.py --backup backup.enc --private-key artifacts/ops-private/backup-recovery.pem --password-file artifacts/ops-private/recovery-password.txt --destination artifacts/ops-private/restored
```

目标目录必须为空；脚本验证认证加密、清单哈希和数据库完整性，不覆盖线上数据。
恢复后的配置与证书含敏感信息，保存在受限目录，不上传日志或Artifact。
2026-10-09 首次服务器备份、GitHub异地导出及从异地Artifact下载后的隔离恢复均已通过；篡改密文验证被拒绝。
Cloudflare Certbot 插件已安装，reload-certificate.sh 可安装为续期deploy hook，尚未接入Token或验证续期。
证书自动续期等待Cloudflare域名限定Token配置，当前证书2027-01-06到期。
