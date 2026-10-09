import 'package:campus_assistant/core/local_store.dart';
import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/core/school.dart';
import 'package:campus_assistant/core/school_picker.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class HistoryService implements ReplyService {
  final List<List<Json>> calls = [];
  @override
  bool get demoMode => false;
  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false, List<Json> history = const []}) async {
    calls.add(history);
    return {'status': 'clarification', 'message': '请继续描述这个事项。'};
  }
}

void main() {
  test('offline school catalogue covers official undergraduate list', () async {
    final catalogue = await loadSchoolCatalogue();
    expect(catalogue.length, 1412);
    expect(catalogue.where((s) => s.matches('qinghuadaxue')).single.id, 'tsinghua');
    expect(catalogue.where((s) => s.matches('4111010001')).single.id, 'pku');
  });
  testWidgets('followups send history and new chat clears context', (tester) async {
    final service = HistoryService();
    await tester.pumpWidget(CampusApp(service: service, store: MemoryStore()));
    await tester.pumpAndSettle();
    for (final question in ['国家奖学金怎么申请？', '那有什么条件？']) {
      await tester.enterText(find.byKey(const Key('question-input')), question);
      await tester.tap(find.byKey(const Key('send-button')));
      await tester.pumpAndSettle();
    }
    expect(service.calls[0], isEmpty);
    expect(service.calls[1].map((t) => t['role']), ['user', 'assistant']);
    await tester.tap(find.byTooltip('新对话')); await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('question-input')), '新事项');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    expect(service.calls.last, isEmpty);
  });
  testWidgets('theme preference persists and can follow system', (tester) async {
    final store = MemoryStore();
    await tester.pumpWidget(CampusApp(service: HistoryService(), store: store));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('外观模式')); await tester.pumpAndSettle();
    await tester.tap(find.text('暗黑模式')); await tester.pumpAndSettle();
    expect(Theme.of(tester.element(find.byKey(const Key('question-input')))).brightness, Brightness.dark);
    expect(store.data['theme'], 'dark');
    await tester.pumpWidget(const SizedBox()); await tester.pumpAndSettle();
    await tester.pumpWidget(CampusApp(service: HistoryService(), store: store)); await tester.pumpAndSettle();
    expect(Theme.of(tester.element(find.byKey(const Key('question-input')))).brightness, Brightness.dark);
    await tester.tap(find.byTooltip('外观模式')); await tester.pumpAndSettle();
    await tester.tap(find.text('跟随系统')); await tester.pumpAndSettle();
    expect(store.data['theme'], 'system');
  });
  testWidgets('school picker filters by name and pinyin', (tester) async {
    final catalogue = await loadSchoolCatalogue();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SchoolPicker(schools: catalogue, selected: 'pku'))));
    await tester.enterText(find.byKey(const Key('school-search')), 'qinghuadaxue'); await tester.pumpAndSettle();
    expect(find.text('清华大学'), findsOneWidget);
    expect(find.text('北京大学'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
