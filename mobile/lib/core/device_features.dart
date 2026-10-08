import 'dart:io';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

class DeviceFeatures {
  final _notifications = FlutterLocalNotificationsPlugin();
  bool _ready = false;

  Future<String?> recognize({required bool camera}) async {
    if (!Platform.isAndroid) throw UnsupportedError('文字识别需在安卓手机上使用');
    final image = await ImagePicker().pickImage(
        source: camera ? ImageSource.camera : ImageSource.gallery, maxWidth: 2400);
    if (image == null) return null;
    return recognizePath(image.path);
  }

  Future<String?> recoverPhoto() async {
    if (!Platform.isAndroid) return null;
    final response = await ImagePicker().retrieveLostData();
    if (response.files?.isNotEmpty == true) return recognizePath(response.files!.first.path);
    return null;
  }

  Future<String> recognizePath(String path) async {
    final recognizer = TextRecognizer(script: TextRecognitionScript.chinese);
    try {
      return (await recognizer.processImage(InputImage.fromFilePath(path))).text;
    } finally { await recognizer.close(); }
  }

  Future<void> _initialize() async {
    if (!Platform.isAndroid) throw UnsupportedError('本地通知需在安卓手机上使用');
    if (_ready) return;
    tzdata.initializeTimeZones();
    await _notifications.initialize(const InitializationSettings(
        android: AndroidInitializationSettings('campus_notification')));
    _ready = true;
  }

  Future<void> schedule(int id, String title, DateTime date) async {
    await _initialize();
    final android = _notifications.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    final allowed = await android?.requestNotificationsPermission();
    if (allowed == false) throw StateError('请在系统设置中允许校园万事通发送通知');
    if (!date.isAfter(DateTime.now())) throw StateError('请选择未来的提醒时间');
    await _notifications.zonedSchedule(id, title, '请查看已保存的办事资料，确认最新要求。',
        tz.TZDateTime.from(date.toUtc(), tz.UTC),
        const NotificationDetails(android: AndroidNotificationDetails(
            'campus_reminders', '办事提醒', channelDescription: '你设置的手机本地办事提醒',
            importance: Importance.high, priority: Priority.high)),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle);
  }

  Future<void> cancel(int id) async { await _initialize(); await _notifications.cancel(id); }
}
