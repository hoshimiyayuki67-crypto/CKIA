import 'dart:io';

import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('demo opens with explicit synthetic-data label', (tester) async {
    await tester.pumpWidget(CampusApp(service: DemoReplyService()));
    expect(find.text('校园万事通'), findsOneWidget);
    expect(find.textContaining('不是学校规定'), findsOneWidget);
  });

  testWidgets('question renders source-backed demo card and checklist', (tester) async {
    await tester.pumpWidget(CampusApp(service: DemoReplyService()));
    await tester.enterText(find.byKey(const Key('question-input')), '测试借书');
    await tester.tap(find.byKey(const Key('send-button')));
    await tester.pumpAndSettle();
    expect(find.text('测试馆借阅'), findsOneWidget);
    final checkbox = find.byKey(const Key('material-0'));
    await tester.ensureVisible(checkbox);
    await tester.tap(checkbox);
    await tester.pumpAndSettle();
    expect(tester.widget<CheckboxListTile>(checkbox).value, isTrue);
  });

  testWidgets('unrelated question and incorrect category refuse', (tester) async {
    // Use the shipped fixture without reusing another test's AssetBundle cache.
    final fixture = File('assets/demo-library.json').readAsStringSync();
    final service = DemoReplyService(loadRecord: () async => fixture);
    final unrelated = await tester.runAsync(() => service.ask('今天天气如何？', null));
    expect(unrelated!['status'], 'refusal');
    final wrongCategory = await tester.runAsync(() => service.ask('测试借书', '教务'));
    expect(wrongCategory!['status'], 'refusal');
  });
}
