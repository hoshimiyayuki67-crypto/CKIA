# Flutter 开发

交付目标为 Android APK。当前已实现 Flutter 原生对话、类别筛选、卡片与材料勾选；H5 是独立辅助预览，不是最终交付物。

## GitHub Actions 构建

仓库 `.github/workflows/android.yml` 在 main 的客户端变更、PR 和手动触发时运行：固定 Flutter 3.35.7 + Java 17 → 生成 Android 平台 → 静态分析 → Flutter 测试 → release APK → 上传 Artifacts。

进入 GitHub 仓库 Actions，选择 Android APK，打开成功的运行，下载 `campus-assistant-android-<运行号>`，解压得到 `campus-assistant.apk` 和 SHA256SUMS.txt。构建产物保留 30 天。

main 和版本标签默认构建在线模式，连接已部署的 HTTPS 后端；PR 构建为明确标注的离线演示。手动 Run workflow 可选择 demo_mode 和 HTTPS api_base_url。模型密钥始终留在服务端。

`v*` 标签触发同一套分析、测试与 APK 构建；成功后发布 GitHub Release，附 APK 和 SHA256SUMS.txt。标签版本必须与 pubspec.yaml 一致。UI 测试导出首页、对话与小屏幕截图至独立 ui-previews Artifact，发布前进行目视检查。

当前 APK 使用 Flutter 模板开发签名，可用于安装测试；正式发布前配置团队固定签名。不同 CI 运行的开发签名可能不同，覆盖安装失败时需要卸载旧测试版（会清空本地状态）。

## 本地构建

本机尚未安装 Flutter，当前将 Android 平台目录由固定 SDK 在 CI 中生成，避免手写 Gradle/Wrapper 版本不匹配。安装 Flutter 3.35.7 和 Android SDK 后可从根目录执行：

```powershell
Set-Location mobile
flutter doctor
flutter create --no-pub --platforms=android --project-name=campus_assistant --org=com.muyuan ../android_template
Copy-Item -Recurse ../android_template/android ./android
python ../scripts/prepare_android.py
flutter pub get
flutter analyze
flutter test
flutter run
flutter build apk --release --dart-define=DEMO_MODE=true
```

平台生成在独立目录中，不覆盖 Dart 源码与业务测试。生成的 mobile/android 默认忽略，平台设置统一由 scripts/prepare_android.py 配置应用中文名及 INTERNET 权限。

在线构建参数：`--dart-define=DEMO_MODE=false --dart-define=API_BASE_URL=https://你的服务地址`。客户端只接受 HTTPS，不在 release 构建启用明文请求。网络错误显示可重试提示，不以离线演示数据代替真实回答。

相机、系统推送、WebView、离线缓存尚未实现。材料勾选和当前消息仅保存在内存中，关闭应用后清空。
