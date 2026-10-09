import 'package:flutter/material.dart';

import 'core/app_theme.dart';
import 'core/reply_service.dart';
import 'core/local_store.dart';
import 'core/device_features.dart';
import 'core/cloud_client.dart';
import 'features/chat/chat_screen.dart';

void main() {
  const demo = bool.fromEnvironment('DEMO_MODE', defaultValue: true);
  const api = String.fromEnvironment('API_BASE_URL');
  WidgetsFlutterBinding.ensureInitialized();
  runApp(CampusApp(service: demo ? DemoReplyService() : ApiReplyService(api),
      store: FileStore(), device: DeviceFeatures(),
      cloud: demo ? null : CloudClient(api, credentials: SecureCredentials(api))));
}

class CampusApp extends StatefulWidget {
  const CampusApp({super.key, required this.service, this.store, this.device, this.cloud});
  final ReplyService service;
  final LocalStore? store;
  final DeviceFeatures? device;
  final CloudClient? cloud;

  @override
  State<CampusApp> createState() => _CampusAppState();
}

class _CampusAppState extends State<CampusApp> {
  ThemeMode _mode = ThemeMode.system;
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '校园万事通',
      debugShowCheckedModeBanner: false,
      theme: campusTheme(), darkTheme: campusTheme(Brightness.dark), themeMode: _mode,
      themeAnimationDuration: const Duration(milliseconds: 220),
      home: ChatScreen(service: widget.service, store: widget.store, device: widget.device,
          cloud: widget.cloud, themeMode: _mode,
          onThemeChanged: (mode) => setState(() => _mode = mode)),
    );
  }
}
