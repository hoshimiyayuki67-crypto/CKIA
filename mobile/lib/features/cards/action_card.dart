import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/app_theme.dart';
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
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SizedBox(height: 18),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(color: CampusColors.mint, borderRadius: BorderRadius.circular(8)),
        child: const Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.fact_check_outlined, size: 14, color: CampusColors.green),
          SizedBox(width: 5),
          Text('办事清单', style: TextStyle(fontSize: 11, color: CampusColors.green)),
        ]),
      ),
      const SizedBox(height: 10),
      Text(field('matter_name'), style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 6),
      Text('适用对象：' + (card['target_users'] as List? ?? []).join('、'),
          style: const TextStyle(fontSize: 12, color: CampusColors.muted)),
      const SizedBox(height: 18),
      Container(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 4),
        decoration: BoxDecoration(color: CampusColors.canvas,
            borderRadius: BorderRadius.circular(16)),
        child: Column(children: [
          Row(children: [
            const Expanded(child: Text('材料清单', style: TextStyle(fontWeight: FontWeight.w600))),
            Text(_checked.length.toString() + '/' + materials.length.toString() + ' 已准备',
                style: const TextStyle(fontSize: 11, color: CampusColors.green)),
          ]),
          const SizedBox(height: 10),
          ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(
            value: materials.isEmpty ? 0 : _checked.length / materials.length,
            minHeight: 3, backgroundColor: CampusColors.line, color: CampusColors.green,
          )),
          for (var i = 0; i < materials.length; i++)
            CheckboxListTile(
              key: Key('material-' + i.toString()),
              dense: true, contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              activeColor: CampusColors.green,
              value: _checked.contains(i),
              onChanged: (value) => setState(() {
                if (value == true) { _checked.add(i); } else { _checked.remove(i); }
              }),
              title: Text(materials[i]['item'] as String? ?? '未查到材料名称',
                  style: const TextStyle(fontSize: 13)),
              subtitle: Text(
                (materials[i]['required'] == true ? '必需材料' : '按需准备') +
                    (materials[i]['note'] is String ? ' · ' + (materials[i]['note'] as String) : ''),
                style: const TextStyle(fontSize: 11, color: CampusColors.muted),
              ),
            ),
        ]),
      ),
      const SizedBox(height: 16),
      _detail(Icons.place_outlined, '办理地点', 'location'),
      _detail(Icons.schedule_rounded, '办公时间', 'office_hours'),
      _detail(Icons.event_outlined, '截止日期', 'deadline'),
      _detail(Icons.route_outlined, '办理方式', 'channel'),
      _detail(Icons.support_agent_rounded, '咨询渠道', 'contact'),
      for (final note in card['notes'] as List? ?? [])
        Container(
          margin: const EdgeInsets.only(top: 4, bottom: 8), padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: const Color(0xFFFFF6E6),
              borderRadius: BorderRadius.circular(12)),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Icon(Icons.lightbulb_outline_rounded, size: 16, color: Color(0xFF967536)),
            const SizedBox(width: 8),
            Expanded(child: Text(note as String,
                style: const TextStyle(fontSize: 12, color: Color(0xFF796235)))),
          ]),
        ),
      const Padding(padding: EdgeInsets.symmetric(vertical: 10), child: Divider(height: 1)),
      const Row(children: [
        Icon(Icons.verified_outlined, size: 15, color: CampusColors.green),
        SizedBox(width: 6),
        Text('信息出处', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      ]),
      const SizedBox(height: 8),
      for (final source in sources) ...[
        Text(source['title'] as String? ?? '未查到出处',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
        Text((source['issuer'] ?? '').toString() + ' · ' + (source['date'] ?? '').toString(),
            style: const TextStyle(fontSize: 11, color: CampusColors.muted)),
        if (source['url'] is String)
          TextButton.icon(
            style: TextButton.styleFrom(padding: EdgeInsets.zero,
                alignment: Alignment.centerLeft, foregroundColor: CampusColors.green),
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: source['url'] as String));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('原文链接已复制')));
              }
            },
            icon: const Icon(Icons.link_rounded, size: 16), label: const Text('复制原文链接'),
          ),
      ],
      const SizedBox(height: 12),
      const Text('勾选仅保存于当前对话，关闭应用后清空。',
          style: TextStyle(fontSize: 10, color: CampusColors.muted)),
    ]);
  }

  Widget _detail(IconData icon, String label, String name) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(icon, size: 16, color: CampusColors.muted),
      const SizedBox(width: 8),
      SizedBox(width: 62, child: Text(label,
          style: const TextStyle(fontSize: 12, color: CampusColors.muted))),
      Expanded(child: Text(field(name), style: const TextStyle(fontSize: 12, height: 1.6))),
    ]),
  );
}
