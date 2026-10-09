import 'dart:io';
import 'dart:ui' as ui;

import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/core/cloud_client.dart';
import 'package:campus_assistant/core/school.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class PreviewService implements ReplyService {
  @override
  bool get demoMode => false;
  bool fail = false;
  bool summary = false;
  int calls = 0;
  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false}) async {
    calls++;
    if (fail) { fail = false; throw const SocketException('preview'); }
    if (summary) return {'status': 'clarification', 'ai_status': 'used',
      'message': '根据院校资料，为你整理如下：',
      'summary_points': [
        {'heading': '办理方式', 'text': '在校生可使用校内自助打印机办理成绩单。需要邮寄纸质材料时，请按官网指引在线申办。',
          'support': [{'reference': 'web-1', 'quote': '在校生可自助办理'}]},
        {'heading': '注意事项', 'text': '毕业生的办理入口与在校生不同，请先确认毕业年份和材料用途，再核对官网最新要求。',
          'support': [{'reference': 'web-1', 'quote': '毕业生需按年份选择办理入口'}]}],
      'web_sources': [{'id': 'web-1', 'title': '成绩单办理指南 · 界面测试数据',
        'url': 'https://pku.edu.cn/service', 'snippet': '在校生可自助办理',
        'retrieved_at': '2026-10-09', 'content_kind': 'page'}]};
    return {'status': 'refusal', 'ai_status': 'used',
      'message': '暂未查到可核实的现行规定。你可以向相关职能部门咨询，我会在资料完善后继续帮你查询。'};
  }
}

void main() {
  testWidgets('mobile layouts export previews without overflow', (tester) async {
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    final fontPath = Platform.environment['UI_PREVIEW_FONT'];
    if (fontPath != null) {
      final bytes = File(fontPath).readAsBytesSync();
      for (final family in ['CampusSans', 'Roboto']) {
        final loader = FontLoader(family)..addFont(Future.value(bytes.buffer.asByteData()));
        await tester.runAsync(loader.load);
      }
      final root = Platform.environment['FLUTTER_ROOT']!;
      final icons = File('$root/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf')
          .readAsBytesSync();
      final iconLoader = FontLoader('MaterialIcons')
        ..addFont(Future.value(icons.buffer.asByteData()));
      await tester.runAsync(iconLoader.load);
    }
    final boundaryKey = GlobalKey();
    Future<void> capture(String name) async {
      expect(tester.takeException(), isNull);
      if (fontPath == null) return;
      final boundary = boundaryKey.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      await tester.runAsync(() async {
        final image = await boundary.toImage(pixelRatio: 2);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final file = File('../artifacts/ui-preview/$name.png');
        file.parent.createSync(recursive: true);
        file.writeAsBytesSync(bytes!.buffer.asUint8List());
        image.dispose();
      });
    }
    final service = PreviewService();
    tester.view.physicalSize = const Size(390, 844);
    await tester.pumpWidget(RepaintBoundary(key: boundaryKey,
        child: CampusApp(service: service)));
    await tester.pumpAndSettle();
    await capture('home');
    await tester.enterText(find.byKey(const Key('question-input')), '奖学金需要准备哪些材料？');
    await tester.tap(find.byKey(const Key('send-button')));
    await tester.pumpAndSettle();
    await capture('conversation');
    await tester.tap(find.byTooltip('新对话'));
    await tester.pumpAndSettle();
    expect(find.text('少一点奔波，\n多一点从容。'), findsOneWidget);
    tester.view.physicalSize = const Size(320, 640);
    await tester.pumpAndSettle();
    await capture('compact');
    tester.view.physicalSize = const Size(390, 1000);
    service.summary = true;
    await tester.enterText(find.byKey(const Key('question-input')), '成绩单怎么办理？');
    await tester.tap(find.byKey(const Key('send-button'))); await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView).last, const Offset(0, 800)); await tester.pumpAndSettle();
    await capture('summary');
    final cloud = CloudClient('https://example.test', credentials: PreviewCredentials());
    await tester.pumpWidget(RepaintBoundary(key: boundaryKey,
        child: CampusApp(service: service, cloud: cloud)));
    await tester.tap(find.byTooltip('账号与云端同步')); await tester.pumpAndSettle();
    await capture('account');
    Navigator.of(tester.element(find.text('把对话带在身边'))).pop(); await tester.pumpAndSettle();
    tester.view.physicalSize = const Size(390, 1100);
    final fixture = File('assets/demo-library.json').readAsStringSync();
    await tester.pumpWidget(RepaintBoundary(key: boundaryKey,
        child: CampusApp(service: DemoReplyService(loadRecord: () async => fixture))));
    await tester.enterText(find.byKey(const Key('question-input')), '测试借书');
    await tester.tap(find.byKey(const Key('send-button')));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView).last, const Offset(0, 900));
    await tester.pumpAndSettle();
    await capture('action-card');
    await tester.tap(find.byTooltip('新对话'));
    await tester.pumpAndSettle();
    tester.view.physicalSize = const Size(320, 640);
    tester.view.viewInsets = const FakeViewPadding(bottom: 260);
    addTearDown(tester.view.resetViewInsets);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('failed query can retry and clear conversation', (tester) async {
    final service = PreviewService()..fail = true;
    await tester.pumpWidget(CampusApp(service: service));
    await tester.enterText(find.byKey(const Key('question-input')), '办理证明');
    await tester.tap(find.byKey(const Key('send-button')));
    await tester.pumpAndSettle();
    expect(find.text('重新查询'), findsOneWidget);
    await tester.tap(find.text('重新查询'));
    await tester.pumpAndSettle();
    expect(service.calls, 2);
    await tester.tap(find.byTooltip('新对话'));
    await tester.pumpAndSettle();
    expect(find.text('办理证明'), findsNothing);
    expect(find.text('少一点奔波，\n多一点从容。'), findsOneWidget);
  });
}

class PreviewCredentials implements CredentialStore {
  @override
  Future<String?> read() async => null;
  @override
  Future<void> write(String? value) async {}
}
