import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/device_features.dart';
import '../../core/local_store.dart';
import '../../core/school.dart';
import '../../core/school_picker.dart';
import '../../core/cloud_client.dart';
import '../../core/motion.dart';

import '../../core/app_theme.dart';
import '../../core/reply_service.dart';
import '../cards/action_card.dart';

part 'chat_tools.dart';
part 'chat_account.dart';

final _categories = ['资助', '教务', '财务', '学籍', '就业', '生活'];
final _icons = [
  Icons.volunteer_activism_outlined, Icons.menu_book_rounded,
  Icons.account_balance_wallet_outlined, Icons.badge_outlined,
  Icons.work_outline_rounded, Icons.local_cafe_outlined,
];
final _descriptions = ['奖助学金 · 助学贷款', '选课 · 考试 · 成绩', '缴费 · 报销 · 票据',
  '证明 · 学籍 · 转专业', '实习 · 就业 · 档案', '住宿 · 图书 · 校园服务'];
final _questions = ['奖学金需要准备哪些材料？', '如何申请成绩单？', '学费缴纳有哪些方式？',
  '在读证明怎么办理？', '毕业生档案如何转接？', '借阅图书需要什么材料？'];

class ChatScreen extends StatefulWidget {
  ChatScreen({super.key, required this.service, this.store, this.device, this.cloud,
      this.themeMode = ThemeMode.system, this.onThemeChanged});
  final ReplyService service;
  final LocalStore? store;
  final DeviceFeatures? device;
  final CloudClient? cloud;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode>? onThemeChanged;
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final List<Json> _messages = [];
  String? _category;
  bool _sending = false;
  bool _loading = false, _searchEnabled = false, _offline = false, _recognizing = false;
  bool _storageHealthy = true;
  School _school = schools.first;
  final List<School> _customSchools = [];
  final List<School> _catalogue = [];
  String _themePreference = 'system';
  final List<Json> _sessions = [], _saved = [], _reminders = [];
  String _sessionId = DateTime.now().microsecondsSinceEpoch.toString();
  final Map<String, List<int>> _checks = {};
  String? _sessionOwner;
  bool _syncing = false;
  String _syncStatus = '本机保存';
  final List<Json> _pendingDeletes = [];

  @override
  void initState() {
    super.initState();
    _loading = widget.store != null;
    _restore();
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send([String? suggestion]) async {
    final question = (suggestion ?? _input.text).trim();
    if (question.isEmpty || _sending || _loading || _syncing) return;
    if (_offline) { _findOffline(question); return; }
    final school = _school;
    final category = _category;
    final search = _searchEnabled;
    final prior = _messages.where((message) => message['school_id'] == school.id
        && message['status'] != 'error').map((message) {
      final text = [message['message'] as String? ?? '',
        if (message['card'] is Map) message['card']['matter_name'] as String? ?? '',
        for (final point in message['summary_points'] as List? ?? []) point['text'] as String? ?? ''].join('\n');
      return <String, dynamic>{'role': message['user'] == true ? 'user' : 'assistant',
        'content': text.length > 1000 ? text.substring(0, 1000) : text};
    }).where((message) => (message['content'] as String).trim().isNotEmpty).toList();
    final history = prior.length > 12 ? prior.sublist(prior.length - 12) : prior;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _messages.add({'user': true, 'message': question, 'school_id': school.id,
          'search_enabled': search});
      _input.clear();
      _sending = true;
    });
    _scrollToEnd();
    _persist();
    try {
      final reply = await widget.service.ask(question, category,
          school: school, searchEnabled: search, history: history);
      if (!mounted) return;
      setState(() => _messages.add({...reply, 'school_id': school.id,
          'saved_at': DateTime.now().toIso8601String()}));
    } catch (_) {
      if (!mounted) return;
      setState(() => _messages.add({
        'status': 'error',
        'message': '暂时无法完成查询，请稍后重试。当前没有获得可核实的答案。',
        'retry_question': question, 'retry_category': category,
      }));
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        _persist();
        _syncCloud();
        _scrollToEnd();
      }
    }
  }

  void _scrollToEnd() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (_scroll.hasClients) {
      _scroll.animateTo(_scroll.position.maxScrollExtent,
          duration: Duration(milliseconds: 250), curve: Curves.easeOut);
    }
  });

  void _newChat() {
    if (_sending || _syncing) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() { _messages.clear(); _input.clear(); _category = null; });
    _sessionId = DateTime.now().microsecondsSinceEpoch.toString();
    _sessionOwner = widget.cloud?.user?['id'] as String?;
    _persist();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      titleSpacing: 20,
      title: Row(children: [
        CampusMark(size: MediaQuery.sizeOf(context).width < 360 ? 30 : 44),
        SizedBox(width: MediaQuery.sizeOf(context).width < 360 ? 8 : 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('校园万事通', style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontSize: MediaQuery.sizeOf(context).width < 360 ? 16 : 20)),
          Text('你的校园办事助手',
              style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted, height: 1.7)),
        ])),
      ]),
      actions: [
        IconButton(tooltip: '账号与云端同步', onPressed: _loading || _sending || _syncing ? null : _account,
            icon: Icon(widget.cloud?.signedIn == true ? Icons.account_circle_rounded : Icons.person_outline_rounded,
                size: 22, color: CampusPalette.of(context).green)),
        IconButton(tooltip: '本地资料与提醒', onPressed: _loading || _sending || _syncing ? null : _library,
            icon: Icon(Icons.inventory_2_outlined, size: 22)),
        IconButton(tooltip: '新对话', onPressed: _sending || _syncing || _loading ? null : _newChat,
            icon: Icon(Icons.add_comment_outlined, size: 22)),
        SizedBox(width: 8),
      ],
    ),
    body: SafeArea(top: false, child: Column(children: [
      _queryControls(),
      Padding(padding: EdgeInsets.fromLTRB(20, 0, 20, 8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(widget.service.demoMode ? Icons.science_outlined : Icons.verified_user_outlined,
              size: 15, color: CampusPalette.of(context).green),
          SizedBox(width: 6),
          Expanded(child: Text(widget.service.demoMode
              ? '演示模式 · 虚构测试数据，不是学校规定。'
              : '依据审核资料 · 信息有出处，办事更安心',
              style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted))),
        ]),
      ),
      SizedBox(height: 48, child: ListView(
        scrollDirection: Axis.horizontal, padding: EdgeInsets.symmetric(horizontal: 20),
        children: ['全部', ..._categories].map((label) {
          final value = label == '全部' ? null : label;
          return Padding(padding: EdgeInsets.only(right: 8), child: ChoiceChip(
            label: Text(label), selected: _category == value,
            onSelected: _sending ? null : (_) => setState(() => _category = value),
          ));
        }).toList(),
      )),
      Expanded(child: AnimatedSwitcher(duration: motionDuration(context, 280),
          child: _loading ? Center(key: ValueKey('loading'), child: CircularProgressIndicator())
          : _messages.isEmpty ? KeyedSubtree(key: ValueKey('welcome'), child: _welcome())
          : KeyedSubtree(key: ValueKey('conversation'), child: _conversation()))),
      _composer(),
    ])),
  );

  Widget _welcome() => ListView(
    padding: EdgeInsets.fromLTRB(20, 16, 20, 24),
    children: [
      Reveal(child: Container(padding: EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: Theme.of(context).brightness == Brightness.dark
              ? [Color(0xFF173D34), Color(0xFF29352A)] : [Color(0xFFD7EEE6), Color(0xFFF1F2D8)],
              begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(28),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(Icons.auto_awesome_rounded, size: 16, color: CampusPalette.of(context).green),
            SizedBox(width: 6),
            Text('校园生活，少一点奔波', style: TextStyle(fontSize: 12, color: CampusPalette.of(context).green)),
          ]),
          SizedBox(height: 16),
          Text('少一点奔波，\n多一点从容。', style: Theme.of(context).textTheme.headlineMedium),
          SizedBox(height: 12),
          Text('读懂官网资料，整理办理步骤。\n从一个问题开始，让事情更简单。',
              style: TextStyle(fontSize: 13, color: CampusPalette.of(context).muted, height: 1.7)),
        ]),
      )),
      SizedBox(height: 24),
      Row(children: [
        Expanded(child: Text('从一件小事开始', style: Theme.of(context).textTheme.titleMedium)),
        Text('点选即可提问', style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted)),
      ]),
      SizedBox(height: 12),
      LayoutBuilder(builder: (context, constraints) {
        final columns = constraints.maxWidth >= 600 ? 3 : 2;
        final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
        return Wrap(spacing: 12, runSpacing: 12, children: [
          for (var i = 0; i < _categories.length; i++)
            if (_category == null || _category == _categories[i])
              SizedBox(width: width, child: Material(
                color: Theme.of(context).colorScheme.surface, borderRadius: BorderRadius.circular(20),
                child: InkWell(borderRadius: BorderRadius.circular(20),
                  onTap: () {
                    setState(() => _category = _categories[i]);
                    _send(widget.service.demoMode && _categories[i] == '生活'
                        ? '测试馆借阅需要什么材料？' : _questions[i]);
                  },
                  child: Padding(padding: EdgeInsets.all(16), child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Icon(_icons[i], color: CampusPalette.of(context).green, size: 23),
                      SizedBox(height: 10),
                      Row(children: [
                        Expanded(child: Text(_categories[i],
                            style: Theme.of(context).textTheme.titleMedium)),
                        Icon(Icons.north_east_rounded, size: 14, color: CampusPalette.of(context).muted),
                      ]),
                      SizedBox(height: 3),
                      Text(_descriptions[i],
                          style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
                    ],
                  )),
                ),
              )),
        ]);
      }),
      SizedBox(height: 20),
      Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(Icons.lightbulb_outline_rounded, size: 16, color: CampusPalette.of(context).muted),
        SizedBox(width: 6),
        Expanded(child: Text('问题越具体，越容易找到相关资料。也可以直接在下方输入。',
            style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted))),
      ]),
    ],
  );

  Widget _conversation() => ListView.builder(
    controller: _scroll, padding: EdgeInsets.fromLTRB(20, 18, 20, 24),
    itemCount: _messages.length + (_sending ? 1 : 0),
    itemBuilder: (context, index) {
      if (index == _messages.length) {
        return SearchPulse(searching: _searchEnabled);
      }
      final item = _messages[index];
      final user = item['user'] == true;
      return Reveal(key: ValueKey('$_sessionId-$index'), child: Padding(padding: EdgeInsets.only(bottom: 22),
        child: Column(crossAxisAlignment: user ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            if (!user) Padding(padding: EdgeInsets.only(bottom: 8), child: Row(children: [
              CampusMark(size: 25), SizedBox(width: 8),
              Text(item['demo_mode'] == true ? '虚构演示' : '校园助手',
                  style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted)),
              if (item['ai_status'] == 'used') ...[
                SizedBox(width: 8),
                Text('AI 辅助', style: TextStyle(fontSize: 10, color: CampusPalette.of(context).green)),
              ],
            ])),
            Container(padding: EdgeInsets.all(18),
              constraints: BoxConstraints(maxWidth: user ? 300 : 680),
              decoration: BoxDecoration(
                color: user ? CampusPalette.of(context).green : Theme.of(context).colorScheme.surface,
                border: user ? null : Border.all(color: CampusPalette.of(context).line),
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(22), topRight: Radius.circular(22),
                  bottomLeft: Radius.circular(user ? 22 : 6),
                  bottomRight: Radius.circular(user ? 6 : 22),
                ),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(item['message'] as String? ?? '未获得可核实的答案',
                    style: TextStyle(fontSize: 14, height: 1.7,
                        color: user ? Theme.of(context).colorScheme.onPrimary : CampusPalette.of(context).ink)),
                if (item['status'] == 'card' && item['card'] is Map)
                  _card(item),
                if (!user) _answerDetails(item),
                if (item['status'] == 'error') TextButton.icon(
                  onPressed: _sending ? null : () {
                    setState(() => _category = item['retry_category'] as String?);
                    _send(item['retry_question'] as String);
                  },
                  icon: Icon(Icons.refresh_rounded, size: 17), label: Text('重新查询'),
                ),
              ]),
            ),
          ],
        ),
      ));
    },
  );

  Widget _composer() => Container(
    padding: EdgeInsets.fromLTRB(16, 12, 16, 10),
    decoration: BoxDecoration(color: CampusPalette.of(context).canvas,
        border: Border(top: BorderSide(color: CampusPalette.of(context).line))),
    child: Column(children: [
      Container(padding: EdgeInsets.fromLTRB(16, 4, 6, 4),
        decoration: BoxDecoration(color: Theme.of(context).colorScheme.surface, borderRadius: BorderRadius.circular(24),
            border: Border.all(color: CampusPalette.of(context).line)),
        child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          IconButton(tooltip: '拍照或图片识别', onPressed: _sending || _recognizing || _loading
              ? null : _photo, icon: _recognizing
                  ? SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : Icon(Icons.document_scanner_outlined, size: 21)),
          Expanded(child: TextField(
            key: Key('question-input'), controller: _input,
            minLines: 1, maxLines: 4, maxLength: 2000, enabled: !_sending && !_syncing && !_loading,
            style: TextStyle(fontSize: 14),
            decoration: InputDecoration(
              hintText: '说说你想办的事…', counterText: '', filled: false,
              contentPadding: EdgeInsets.symmetric(vertical: 12), border: InputBorder.none,
              enabledBorder: InputBorder.none, focusedBorder: InputBorder.none,
              disabledBorder: InputBorder.none,
              hintStyle: TextStyle(color: CampusPalette.of(context).muted, fontSize: 13),
            ),
          )),
          Padding(padding: EdgeInsets.only(bottom: 4), child: SizedBox(
            width: 44, height: 44,
            child: FilledButton(key: Key('send-button'),
              onPressed: _sending || _loading || _syncing ? null : () => _send(),
              style: FilledButton.styleFrom(padding: EdgeInsets.zero),
              child: Tooltip(message: '发送', child: Icon(Icons.arrow_upward_rounded, size: 22)),
            ),
          )),
        ]),
      ),
      SizedBox(height: 8),
      Text('AI 辅助查询，请以学校职能部门答复为准',
          style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
    ]),
  );
}
