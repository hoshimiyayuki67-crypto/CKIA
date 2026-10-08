# Flutter 开发

当前包含 pubspec 和 Dart 入口，Android 平台工程需在安装 Flutter 后生成：

```powershell
Set-Location mobile
flutter doctor
flutter create --platforms=android --project-name campus_assistant --org com.muyuan .
flutter pub get
flutter analyze
flutter run
```

平台生成后检查 `lib/main.dart`、`pubspec.yaml` 和生成的 `test/widget_test.dart`。模板测试通常断言计数器；将其替换为实际入口测试后执行 `flutter test`。保留本项目入口和依赖定义，生成结果需评审。

后续 API 地址由 `--dart-define=API_BASE_URL=...` 注入并在 core/api 中读取。Android 模拟器访问宿主机用 `10.0.2.2:8000`；真机使用开发电脑局域网地址，并将后端监听改为 `0.0.0.0`。开发 HTTP 例外限定调试构建，正式构建使用 HTTPS。

`flutter build apk --release` 在业务链路和签名准备完成后执行。相机、通知权限、WebView、离线缓存尚未实现。
