import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';

import 'school.dart';

typedef Json = Map<String, dynamic>;

abstract class ReplyService {
  bool get demoMode;
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false, List<Json> history = const []});
}

const schoolsFirst = School('imuchuangye', '内蒙古大学创业学院', 'imuchuangye.cn');

class DemoReplyService implements ReplyService {
  DemoReplyService({this.loadRecord});
  final Future<String> Function()? loadRecord;

  @override
  bool get demoMode => true;

  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false, List<Json> history = const []}) async {
    final record = jsonDecode(
      await (loadRecord?.call() ?? rootBundle.loadString('assets/demo-library.json')),
    ) as Json;
    final matches = (record['aliases'] as List).any(
      (alias) => question.contains(alias as String),
    );
    if (school.id != 'imuchuangye' || !matches ||
        (category != null && category != record['category'])) {
      return {
        'status': 'refusal',
        'message': '未查询到可核实的规定，请咨询学校相关职能部门。',
        'demo_mode': true,
      };
    }
    return {
      'status': 'card',
      'message': '以下为虚构测试信息，不是学校规定。',
      'demo_mode': true,
      'card': {
        ...record['fields'] as Json,
        'sources': [record['source']],
      },
    };
  }
}

class ApiReplyService implements ReplyService {
  ApiReplyService(this.baseUrl);
  final String baseUrl;

  @override
  bool get demoMode => false;

  @override
  Future<Json> ask(String question, String? category,
      {School school = schoolsFirst, bool searchEnabled = false, List<Json> history = const []}) async {
    final base = Uri.parse(baseUrl);
    if (base.scheme != 'https' || base.host.isEmpty) {
      throw const FormatException('请配置 HTTPS 后端地址');
    }
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 10);
    try {
      final request = await client.postUrl(
        Uri.parse('${baseUrl.replaceFirst(RegExp(r'/+$'), '')}/api/v1/chat'),
      );
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode({
        'question': question,
        if (category != null) 'category': category,
        'school_id': school.id, 'school_name': school.name,
        'school_domain': school.domain, 'search_enabled': searchEnabled,
        'history': history.length > 12 ? history.sublist(history.length - 12) : history,
      }));
      final response = await request.close().timeout(const Duration(seconds: 110));
      final text = await response.transform(utf8.decoder).join().timeout(
        const Duration(seconds: 15),
      );
      if (response.statusCode != 200) {
        throw HttpException('服务返回 ${response.statusCode}');
      }
      final data = jsonDecode(text) as Json;
      if (!['card', 'refusal', 'clarification'].contains(data['status'])) {
        throw const FormatException('服务响应格式不正确');
      }
      if (data['status'] == 'card' && data['card'] is! Map) {
        throw const FormatException('卡片数据缺失');
      }
      return data;
    } finally {
      client.close(force: true);
    }
  }
}
