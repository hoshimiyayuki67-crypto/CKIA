import 'dart:convert';

import 'package:campus_assistant/core/cloud_client.dart';
import 'package:campus_assistant/core/local_store.dart';
import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/core/school.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class TestCredentials implements CredentialStore {
  String? value;
  @override
  Future<String?> read() async => value;
  @override
  Future<void> write(String? data) async { value = data; }
}

class TestCloud {
  final rows = <String, Json>{};
  final calls = <String>[];
  Future<Json> request(String method, String path, Json? body, String? token) async {
    calls.add('$method $path');
    if (path == '/auth/login' || path == '/auth/register') {
      return {'token': 'secret-token', 'user': {'id': 'u1', 'username': 'alice'}};
    }
    if (token != 'secret-token') throw const CloudError(401, '请登录');
    if (path == '/auth/me') return {'id': 'u1', 'username': 'alice'};
    if (path == '/auth/logout') return {'ok': true};
    if (path == '/sessions') return {'sessions': rows.values.toList()};
    final id = path.split('/').last;
    if (method == 'PUT') {
      if ((rows[id]?['revision'] ?? 0) != body!['revision']) throw const CloudError(409, '冲突');
      final revision = (body['revision'] as int) + 1;
      rows[id] = {'id': id, 'revision': revision, 'data': body['data'], 'deleted': false};
      return {'revision': revision};
    }
    throw StateError('Unexpected request');
  }
}

class SummaryService implements ReplyService {
  @override
  bool get demoMode => false;
  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false, List<Json> history = const []}) async => {
    'status': 'clarification', 'message': '根据院校资料，为你整理如下：',
    'summary_points': [{'heading': '办理方式', 'text': '在校生可使用自助打印机办理成绩单。',
      'support': [{'reference': 'web-1', 'quote': '在校生自助打印'}]}],
    'web_sources': [{'id': 'web-1', 'title': '官网办理指南', 'url': 'https://pku.edu.cn/service',
      'snippet': '原始大段网页内容应折叠显示', 'retrieved_at': '2026-10-09'}],
  };
}

void main() {
  test('credentials restore securely and revoke on logout', () async {
    final saved = TestCredentials(), fake = TestCloud();
    final cloud = CloudClient('https://example.test', credentials: saved, transport: fake.request);
    await cloud.authenticate('alice', 'test-password');
    expect(saved.value, isNot(contains('test-password')));
    final reopened = CloudClient('https://example.test', credentials: saved, transport: fake.request);
    await reopened.restore(); expect(reopened.signedIn, isTrue);
    await reopened.logout(); expect(saved.value, isNull); expect(reopened.signedIn, isFalse);
  });

  testWidgets('new conversations sync without placing credentials in local history', (tester) async {
    final saved = TestCredentials(), fake = TestCloud(), store = MemoryStore();
    final cloud = CloudClient('https://example.test', credentials: saved, transport: fake.request);
    await cloud.authenticate('alice', 'test-password');
    await tester.pumpWidget(CampusApp(service: SummaryService(), store: store, cloud: cloud));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('新对话')); await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('question-input')), '成绩单');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    expect(fake.rows.length, 1);
    expect(fake.rows.values.first['data']['messages'], hasLength(2));
    expect(jsonEncode(store.data), isNot(contains('secret-token')));
    expect(store.data['sessions'][0]['dirty'], isFalse);
    expect(find.text('在校生可使用自助打印机办理成绩单。'), findsOneWidget);
    expect(find.text('原始大段网页内容应折叠显示'), findsNothing);
    await tester.tap(find.text('查看 1 份来源与原文')); await tester.pumpAndSettle();
    expect(find.text('原始大段网页内容应折叠显示'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('concurrent cloud changes retain both versions', (tester) async {
    final saved = TestCredentials(), fake = TestCloud(), store = MemoryStore();
    final cloud = CloudClient('https://example.test', credentials: saved, transport: fake.request);
    await cloud.authenticate('alice', 'test-password');
    final local = {'id': 'old', 'owner': 'u1', 'cloud_revision': 1, 'dirty': true,
      'title': '本机修改', 'school': schoolsFirst.toJson(), 'category': null,
      'updated_at': '2026-10-09', 'messages': [{'user': true, 'message': '本机修改'}]};
    store.data = {'version': 1, 'sessions': [local]};
    fake.rows['old'] = {'id': 'old', 'revision': 2, 'deleted': false,
      'data': {...local, 'title': '其他设备修改', 'messages': [{'user': true, 'message': '其他设备修改'}]}};
    await tester.pumpWidget(CampusApp(service: SummaryService(), store: store, cloud: cloud));
    await tester.pumpAndSettle();
    expect(fake.rows.length, 2);
    expect((store.data['sessions'] as List).map((s) => s['title']).toSet(),
        {'本机修改', '其他设备修改'});
  });
}
