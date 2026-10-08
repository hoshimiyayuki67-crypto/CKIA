import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/reply_service.dart';

class ActionCardView extends StatefulWidget {
  const ActionCardView({super.key, required this.card});
  final Json card;

  @override
  State<ActionCardView> createState() => _ActionCardViewState();
}

class _ActionCardViewState extends State<ActionCardView> {
  final Set<int> _checked = {};

  String field(String name) => widget.card[name] as String? ?? '未查到明确信息';

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    final materials = card['materials'] as List? ?? [];
    final sources = card['sources'] as List? ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        Text(field('matter_name'), style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        Text('适用对象：${(card['target_users'] as List? ?? []).join('、')}'),
        const SizedBox(height: 12),
        const Text('材料清单'),
        for (var i = 0; i < materials.length; i++)
          CheckboxListTile(
            key: Key('material-$i'),
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _checked.contains(i),
            onChanged: (value) => setState(() {
              if (value == true) { _checked.add(i); } else { _checked.remove(i); }
            }),
            title: Text(materials[i]['item'] as String? ?? '未查到材料名称'),
            subtitle: Text(materials[i]['required'] == true ? '必需材料' : '按需准备'),
          ),
        for (final entry in {
          '办理地点': 'location', '办公时间': 'office_hours', '截止日期': 'deadline',
          '办理方式': 'channel', '咨询渠道': 'contact',
        }.entries)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text('${entry.key}：${field(entry.value)}'),
          ),
        for (final note in card['notes'] as List? ?? [])
          Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(note as String)),
        const Divider(),
        for (final source in sources) ...[
          Text(source['title'] as String? ?? '未查到出处'),
          Text('${source['issuer']} · ${source['date']}'),
          if (source['url'] is String)
            TextButton(
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: source['url'] as String));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('原文链接已复制')),
                  );
                }
              },
              child: const Text('复制原文链接'),
            ),
        ],
        const SizedBox(height: 8),
        Text('勾选仅保存于当前对话，关闭应用后清空。', style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}
