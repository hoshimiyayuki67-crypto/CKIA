import 'package:flutter/material.dart';

import '../../core/app_theme.dart';
import '../../core/reply_service.dart';
import '../cards/action_card.dart';

const _categories = ['资助', '教务', '财务', '学籍', '就业', '生活'];
const _icons = [
  Icons.volunteer_activism_outlined, Icons.menu_book_rounded,
  Icons.account_balance_wallet_outlined, Icons.badge_outlined,
  Icons.work_outline_rounded, Icons.local_cafe_outlined,
];
const _descriptions = ['奖助学金 · 助学贷款', '选课 · 考试 · 成绩', '缴费 · 报销 · 票据',
  '证明 · 学籍 · 转专业', '实习 · 就业 · 档案', '住宿 · 图书 · 校园服务'];
const _questions = ['奖学金需要准备哪些材料？', '如何申请成绩单？', '学费缴纳有哪些方式？',
  '在读证明怎么办理？', '毕业生档案如何转接？', '借阅图书需要什么材料？'];

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.service});
  final ReplyService service;
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final List<Json> _messages = [];
  String? _category;
  bool _sending = false;

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send([String? suggestion]) async {
    final question = (suggestion ?? _input.text).trim();
    if (question.isEmpty || _sending) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _messages.add({'user': true, 'message': question});
      _input.clear();
      _sending = true;
    });
    _scrollToEnd();
    try {
      final reply = await widget.service.ask(question, _category);
      if (!mounted) return;
      setState(() => _messages.add(reply));
    } catch (_) {
      if (!mounted) return;
      setState(() => _messages.add({
        'status': 'error',
        'message': '暂时无法完成查询，请稍后重试。当前没有获得可核实的答案。',
        'retry_question': question, 'retry_category': _category,
      }));
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        _scrollToEnd();
      }
    }
  }

  void _scrollToEnd() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (_scroll.hasClients) {
      _scroll.animateTo(_scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
    }
  });

  void _newChat() {
    if (_sending) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() { _messages.clear(); _input.clear(); _category = null; });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      titleSpacing: 20,
      title: Row(children: [
        const CampusMark(),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('校园万事通', style: Theme.of(context).textTheme.titleLarge),
          const Text('你的校园办事助手',
              style: TextStyle(fontSize: 11, color: CampusColors.muted, height: 1.7)),
        ])),
      ]),
      actions: [
        IconButton(tooltip: '新对话', onPressed: _sending ? null : _newChat,
            icon: const Icon(Icons.add_comment_outlined, size: 22)),
        IconButton(
          tooltip: '使用说明', icon: const Icon(Icons.info_outline_rounded, size: 22),
          onPressed: () => showAboutDialog(
            context: context, applicationName: '校园万事通', applicationVersion: '0.3.0',
            applicationIcon: const CampusMark(),
            children: const [Text('根据已审核资料提供办事信息，没有依据时明确告知。'
                '请以学校职能部门答复为准。消息与材料勾选仅保存在当前会话。')],
          ),
        ),
        const SizedBox(width: 8),
      ],
    ),
    body: SafeArea(top: false, child: Column(children: [
      Padding(padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(widget.service.demoMode ? Icons.science_outlined : Icons.verified_user_outlined,
              size: 15, color: CampusColors.green),
          const SizedBox(width: 6),
          Expanded(child: Text(widget.service.demoMode
              ? '演示模式 · 虚构测试数据，不是学校规定。'
              : '依据审核资料 · 信息有出处，办事更安心',
              style: const TextStyle(fontSize: 11, color: CampusColors.muted))),
        ]),
      ),
      SizedBox(height: 48, child: ListView(
        scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 20),
        children: ['全部', ..._categories].map((label) {
          final value = label == '全部' ? null : label;
          return Padding(padding: const EdgeInsets.only(right: 8), child: ChoiceChip(
            label: Text(label), selected: _category == value,
            onSelected: _sending ? null : (_) => setState(() => _category = value),
          ));
        }).toList(),
      )),
      Expanded(child: _messages.isEmpty ? _welcome() : _conversation()),
      _composer(),
    ])),
  );

  Widget _welcome() => ListView(
    padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
    children: [
      Container(padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFFE4F2E7), Color(0xFFF0F4DC)],
              begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(28),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Row(children: [
            Icon(Icons.auto_awesome_rounded, size: 16, color: CampusColors.green),
            SizedBox(width: 6),
            Text('校园生活，少一点奔波', style: TextStyle(fontSize: 12, color: CampusColors.green)),
          ]),
          const SizedBox(height: 16),
          Text('办事有方向，\n校园更轻松。', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 12),
          const Text('材料、地点、时间与出处，\n帮你把办事信息整理清楚。',
              style: TextStyle(fontSize: 13, color: CampusColors.muted, height: 1.7)),
        ]),
      ),
      const SizedBox(height: 24),
      Row(children: [
        Expanded(child: Text('从一件小事开始', style: Theme.of(context).textTheme.titleMedium)),
        const Text('点选即可提问', style: TextStyle(fontSize: 11, color: CampusColors.muted)),
      ]),
      const SizedBox(height: 12),
      LayoutBuilder(builder: (context, constraints) {
        final columns = constraints.maxWidth >= 600 ? 3 : 2;
        final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
        return Wrap(spacing: 12, runSpacing: 12, children: [
          for (var i = 0; i < _categories.length; i++)
            if (_category == null || _category == _categories[i])
              SizedBox(width: width, child: Material(
                color: Colors.white, borderRadius: BorderRadius.circular(20),
                child: InkWell(borderRadius: BorderRadius.circular(20),
                  onTap: () {
                    setState(() => _category = _categories[i]);
                    _send(widget.service.demoMode && _categories[i] == '生活'
                        ? '测试馆借阅需要什么材料？' : _questions[i]);
                  },
                  child: Padding(padding: const EdgeInsets.all(16), child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Icon(_icons[i], color: CampusColors.green, size: 23),
                      const SizedBox(height: 10),
                      Row(children: [
                        Expanded(child: Text(_categories[i],
                            style: Theme.of(context).textTheme.titleMedium)),
                        const Icon(Icons.north_east_rounded, size: 14, color: CampusColors.muted),
                      ]),
                      const SizedBox(height: 3),
                      Text(_descriptions[i],
                          style: const TextStyle(fontSize: 10, color: CampusColors.muted)),
                    ],
                  )),
                ),
              )),
        ]);
      }),
      const SizedBox(height: 20),
      const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(Icons.lightbulb_outline_rounded, size: 16, color: CampusColors.muted),
        SizedBox(width: 6),
        Expanded(child: Text('问题越具体，越容易找到相关资料。也可以直接在下方输入。',
            style: TextStyle(fontSize: 11, color: CampusColors.muted))),
      ]),
    ],
  );

  Widget _conversation() => ListView.builder(
    controller: _scroll, padding: const EdgeInsets.fromLTRB(20, 18, 20, 24),
    itemCount: _messages.length + (_sending ? 1 : 0),
    itemBuilder: (context, index) {
      if (index == _messages.length) {
        return const Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Row(children: [
          SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
          SizedBox(width: 10),
          Text('正在查找相关资料…', style: TextStyle(fontSize: 12, color: CampusColors.muted)),
        ]));
      }
      final item = _messages[index];
      final user = item['user'] == true;
      return Padding(padding: const EdgeInsets.only(bottom: 22),
        child: Column(crossAxisAlignment: user ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            if (!user) Padding(padding: const EdgeInsets.only(bottom: 8), child: Row(children: [
              const CampusMark(size: 25), const SizedBox(width: 8),
              Text(item['demo_mode'] == true ? '虚构演示' : '校园助手',
                  style: const TextStyle(fontSize: 11, color: CampusColors.muted)),
              if (item['ai_status'] == 'used') ...[
                const SizedBox(width: 8),
                const Text('AI 辅助', style: TextStyle(fontSize: 10, color: CampusColors.green)),
              ],
            ])),
            Container(padding: const EdgeInsets.all(18),
              constraints: BoxConstraints(maxWidth: user ? 300 : 680),
              decoration: BoxDecoration(
                color: user ? CampusColors.green : Colors.white,
                border: user ? null : Border.all(color: CampusColors.line),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(22), topRight: const Radius.circular(22),
                  bottomLeft: Radius.circular(user ? 22 : 6),
                  bottomRight: Radius.circular(user ? 6 : 22),
                ),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(item['message'] as String? ?? '未获得可核实的答案',
                    style: TextStyle(fontSize: 14, height: 1.7,
                        color: user ? Colors.white : CampusColors.ink)),
                if (item['status'] == 'card' && item['card'] is Map)
                  ActionCardView(card: Map<String, dynamic>.from(item['card'] as Map)),
                if (item['status'] == 'error') TextButton.icon(
                  onPressed: _sending ? null : () {
                    setState(() => _category = item['retry_category'] as String?);
                    _send(item['retry_question'] as String);
                  },
                  icon: const Icon(Icons.refresh_rounded, size: 17), label: const Text('重新查询'),
                ),
              ]),
            ),
          ],
        ),
      );
    },
  );

  Widget _composer() => Container(
    padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
    decoration: const BoxDecoration(color: CampusColors.canvas,
        border: Border(top: BorderSide(color: CampusColors.line))),
    child: Column(children: [
      Container(padding: const EdgeInsets.fromLTRB(16, 4, 6, 4),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24),
            border: Border.all(color: CampusColors.line)),
        child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Expanded(child: TextField(
            key: const Key('question-input'), controller: _input,
            minLines: 1, maxLines: 4, maxLength: 2000, enabled: !_sending,
            style: const TextStyle(fontSize: 14),
            decoration: const InputDecoration(
              hintText: '想办什么事？在这里问我', counterText: '', border: InputBorder.none,
              hintStyle: TextStyle(color: CampusColors.muted, fontSize: 13),
            ),
          )),
          Padding(padding: const EdgeInsets.only(bottom: 4), child: SizedBox(
            width: 44, height: 44,
            child: FilledButton(key: const Key('send-button'),
              onPressed: _sending ? null : () => _send(),
              style: FilledButton.styleFrom(padding: EdgeInsets.zero),
              child: const Tooltip(message: '发送', child: Icon(Icons.arrow_upward_rounded, size: 22)),
            ),
          )),
        ]),
      ),
      const SizedBox(height: 8),
      const Text('AI 辅助查询，请以学校职能部门答复为准',
          style: TextStyle(fontSize: 10, color: CampusColors.muted)),
    ]),
  );
}
