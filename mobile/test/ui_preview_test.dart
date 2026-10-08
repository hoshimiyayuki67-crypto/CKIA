import 'dart:io';
import 'dart:ui' as ui;

import 'package:campus_assistant/core/reply_service.dart';
import 'package:campus_assistant/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class PreviewService implements ReplyService {
  @override
  bool get demoMode => false;
  bool fail = false;
  int calls = 0;
  @override
  Future<Json> ask(String question, String? category) async {
    calls++;
    if (fail) { fail = false; throw const SocketException('preview'); }
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
      final loader = FontLoader('CampusSans')..addFont(Future.value(bytes.buffer.asByteData()));
      await tester.runAsync(loader.load);
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
    expect(find.text('从一件小事开始'), findsOneWidget);
    tester.view.physicalSize = const Size(320, 640);
    await tester.pumpAndSettle();
    await capture('compact');
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
    expect(find.text('从一件小事开始'), findsOneWidget);
  });
}
