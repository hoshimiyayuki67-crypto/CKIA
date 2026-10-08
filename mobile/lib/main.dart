import 'package:flutter/material.dart';

import 'core/app_theme.dart';
import 'core/reply_service.dart';
import 'features/chat/chat_screen.dart';

void main() {
  const demo = bool.fromEnvironment('DEMO_MODE', defaultValue: true);
  const api = String.fromEnvironment('API_BASE_URL');
  runApp(CampusApp(service: demo ? DemoReplyService() : ApiReplyService(api)));
}

class CampusApp extends StatelessWidget {
  const CampusApp({super.key, required this.service});
  final ReplyService service;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '校园万事通',
      debugShowCheckedModeBanner: false,
      theme: campusTheme(),
      home: ChatScreen(service: service),
    );
  }
}
