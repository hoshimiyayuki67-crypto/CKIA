import 'package:flutter/material.dart';

import 'core/app_theme.dart';
import 'core/reply_service.dart';
import 'core/local_store.dart';
import 'core/device_features.dart';
import 'features/chat/chat_screen.dart';

void main() {
  const demo = bool.fromEnvironment('DEMO_MODE', defaultValue: true);
  const api = String.fromEnvironment('API_BASE_URL');
  WidgetsFlutterBinding.ensureInitialized();
  runApp(CampusApp(service: demo ? DemoReplyService() : ApiReplyService(api),
      store: FileStore(), device: DeviceFeatures()));
}

class CampusApp extends StatelessWidget {
  const CampusApp({super.key, required this.service, this.store, this.device});
  final ReplyService service;
  final LocalStore? store;
  final DeviceFeatures? device;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '校园万事通',
      debugShowCheckedModeBanner: false,
      theme: campusTheme(),
      home: ChatScreen(service: service, store: store, device: device),
    );
  }
}
