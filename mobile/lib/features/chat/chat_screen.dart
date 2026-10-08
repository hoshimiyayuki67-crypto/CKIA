import 'package:flutter/material.dart';

import '../../core/reply_service.dart';
import '../cards/action_card.dart';

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

  Future<void> _send() async {
    final question = _input.text.trim();
    if (question.isEmpty || _sending) return;
    setState(() {
      _messages.add({'user': true, 'message': question});
      _input.clear();
      _sending = true;
    });
    try {
      final reply = await widget.service.ask(question, _category);
      if (!mounted) return;
      setState(() => _messages.add(reply));
    } catch (_) {
      if (!mounted) return;
      setState(() => _messages.add({
        'message': '暂时无法完成查询，请检查网络或后端配置。当前没有获得可核实的答案。',
      }));
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_scroll.hasClients) {
            _scroll.animateTo(
              _scroll.position.maxScrollExtent,
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeOut,
            );
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('校园万事通'),
        actions: [
          IconButton(
            tooltip: '应用说明',
            icon: const Icon(Icons.info_outline),
            onPressed: () => showAboutDialog(
              context: context,
              applicationName: '校园万事通',
              applicationVersion: '0.2.0 开发预览',
              children: const [Text('AI 辅助整理，请以学校职能部门答复为准。截图、推送和离线保存仍待接入。')],
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(widget.service.demoMode
                  ? '演示模式 · 仅含虚构测试数据，不是学校规定。\n可提问“测试馆借阅需要什么材料？”'
                  : '依据已审核资料回答，查不到时明确告知。'),
            ),
            SizedBox(
              height: 48,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: ['全部', '资助', '教务', '财务', '学籍', '就业', '生活'].map((label) {
                  final value = label == '全部' ? null : label;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(label),
                      selected: _category == value,
                      onSelected: _sending ? null : (_) => setState(() => _category = value),
                    ),
                  );
                }).toList(),
              ),
            ),
            Expanded(
              child: ListView.builder(
                controller: _scroll,
                padding: const EdgeInsets.all(16),
                itemCount: _messages.length + 1,
                itemBuilder: (context, index) {
                  if (index == 0) {
                    return const Padding(
                      padding: EdgeInsets.only(bottom: 16),
                      child: Text('想了解什么校园事务？我会帮你整理材料、地点、时间和出处。'),
                    );
                  }
                  final item = _messages[index - 1];
                  final user = item['user'] == true;
                  return Align(
                    alignment: user ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: user
                            ? Theme.of(context).colorScheme.primaryContainer
                            : Theme.of(context).colorScheme.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (!user) Text(
                            item['demo_mode'] == true ? '虚构演示 · AI 辅助整理' : 'AI 辅助整理',
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                          Text(item['message'] as String? ?? '未获得可核实的答案'),
                          if (item['status'] == 'card' && item['card'] is Map)
                            ActionCardView(card: Map<String, dynamic>.from(item['card'] as Map)),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('question-input'),
                      controller: _input,
                      minLines: 1,
                      maxLines: 4,
                      maxLength: 2000,
                      enabled: !_sending,
                      decoration: const InputDecoration(
                        hintText: '输入你想办理的事项',
                        counterText: '',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    key: const Key('send-button'),
                    onPressed: _sending ? null : _send,
                    child: Text(_sending ? '查询中' : '发送'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
