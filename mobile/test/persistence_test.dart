import 'dart:io';

import 'package:campus_assistant/core/local_store.dart';
import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/core/school.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class RecordingService implements ReplyService {
  int calls = 0;
  School? selected;
  bool? search;
  @override
  bool get demoMode => false;
  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false}) async {
    calls++; selected = school; search = searchEnabled;
    return {'status': 'refusal', 'message': '已保存的测试通知'};
  }
}

void main() {
  test('file store survives restart, serializes writes and recovers damaged primary', () async {
    final directory = await Directory.systemTemp.createTemp('campus-store-');
    try {
      final store = FileStore(directory: () async => directory);
      await Future.wait([store.write({'sessions': [1]}), store.write({'sessions': [2]})]);
      expect((await FileStore(directory: () async => directory).read())['sessions'], [2]);
      await File('${directory.path}/campus-state.json').writeAsString('{broken');
      expect((await store.read())['sessions'], [1]);
      await File('${directory.path}/campus-state.json.bak').writeAsString('{broken');
      await expectLater(store.read(), throwsFormatException);
    } finally { await directory.delete(recursive: true); }
  });

  testWidgets('conversation and checklist survive restart and historical reopening', (tester) async {
    final store = MemoryStore();
    final fixture = File('assets/demo-library.json').readAsStringSync();
    final service = DemoReplyService(loadRecord: () async => fixture);
    await tester.pumpWidget(CampusApp(service: service, store: store));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('question-input')), '测试借书');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    final checkbox = find.byKey(const Key('material-0'));
    await Scrollable.ensureVisible(tester.element(checkbox), alignment: .5); await tester.pumpAndSettle();
    await tester.tap(checkbox); await tester.pumpAndSettle();
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(CampusApp(service: service, store: store)); await tester.pumpAndSettle();
    await Scrollable.ensureVisible(tester.element(checkbox), alignment: .5); await tester.pumpAndSettle();
    expect(tester.widget<CheckboxListTile>(checkbox).value, isTrue);
    await tester.tap(find.byTooltip('新对话')); await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('本地资料与提醒')); await tester.pumpAndSettle();
    await tester.tap(find.text('测试借书')); await tester.pumpAndSettle();
    expect(find.text('测试馆借阅'), findsOneWidget);
    expect(tester.widget<CheckboxListTile>(checkbox).value, isTrue);
  });

  testWidgets('school and search are sent precisely; offline mode never calls service', (tester) async {
    final service = RecordingService();
    final store = MemoryStore();
    await tester.pumpWidget(CampusApp(service: service, store: store)); await tester.pumpAndSettle();
    await tester.tap(find.text('内蒙古大学创业学院')); await tester.pumpAndSettle();
    await tester.tap(find.text('北京大学')); await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('search-switch'))); await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('question-input')), '测试通知');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    expect(service.selected!.id, 'pku'); expect(service.search, isTrue);
    await tester.tap(find.byKey(const Key('offline-switch'))); await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('question-input')), '通知');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    expect(service.calls, 1); expect(find.text('离线查询结果'), findsOneWidget);
    expect(find.text('已保存的测试通知'), findsOneWidget);
  });
}
