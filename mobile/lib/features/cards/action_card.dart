import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/app_theme.dart';
import '../../core/reply_service.dart';

class ActionCardView extends StatefulWidget {
  ActionCardView({super.key, required this.card, this.checked,
    this.onChecked, this.onSave, this.onReminder});
  final Json card;
  final List<int>? checked;
  final ValueChanged<List<int>>? onChecked;
  final VoidCallback? onSave, onReminder;
  @override
  State<ActionCardView> createState() => _ActionCardViewState();
}

class _ActionCardViewState extends State<ActionCardView> {
  final Set<int> _checked = {};
  Set<int> get checked => _checked;
  @override
  void initState() { super.initState(); _checked.addAll(widget.checked ?? []); }
  @override
  void didUpdateWidget(covariant ActionCardView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.checked != null) { _checked.clear(); _checked.addAll(widget.checked!); }
  }
  String field(String name) => widget.card[name] as String? ?? '未查到明确信息';

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    final materials = card['materials'] as List? ?? [];
    final sources = card['sources'] as List? ?? [];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(height: 18),
      Container(
        padding: EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(color: CampusPalette.of(context).mint, borderRadius: BorderRadius.circular(8)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.fact_check_outlined, size: 14, color: CampusPalette.of(context).green),
          SizedBox(width: 5),
          Text('办事清单', style: TextStyle(fontSize: 11, color: CampusPalette.of(context).green)),
        ]),
      ),
      SizedBox(height: 10),
      Text(field('matter_name'), style: Theme.of(context).textTheme.titleLarge),
      SizedBox(height: 6),
      Text('适用对象：' + (card['target_users'] as List? ?? []).join('、'),
          style: TextStyle(fontSize: 12, color: CampusPalette.of(context).muted)),
      SizedBox(height: 18),
      Container(
        padding: EdgeInsets.fromLTRB(14, 14, 14, 4),
        decoration: BoxDecoration(color: CampusPalette.of(context).canvas,
            borderRadius: BorderRadius.circular(16)),
        child: Column(children: [
          Row(children: [
            Expanded(child: Text('材料清单', style: TextStyle(fontWeight: FontWeight.w600))),
            Text(checked.length.toString() + '/' + materials.length.toString() + ' 已准备',
                style: TextStyle(fontSize: 11, color: CampusPalette.of(context).green)),
          ]),
          SizedBox(height: 10),
          ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(
            value: materials.isEmpty ? 0 : checked.length / materials.length,
            minHeight: 3, backgroundColor: CampusPalette.of(context).line, color: CampusPalette.of(context).green,
          )),
          for (var i = 0; i < materials.length; i++)
            CheckboxListTile(
              key: Key('material-' + i.toString()),
              dense: true, contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              activeColor: CampusPalette.of(context).green,
              value: checked.contains(i),
              onChanged: (value) => setState(() {
                final next = Set<int>.from(checked);
                if (value == true) { next.add(i); } else { next.remove(i); }
                _checked.clear(); _checked.addAll(next);
                widget.onChecked?.call(next.toList()..sort());
              }),
              title: Text(materials[i]['item'] as String? ?? '未查到材料名称',
                  style: TextStyle(fontSize: 13)),
              subtitle: Text(
                (materials[i]['required'] == true ? '必需材料' : '按需准备') +
                    (materials[i]['note'] is String ? ' · ' + (materials[i]['note'] as String) : ''),
                style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted),
              ),
            ),
        ]),
      ),
      SizedBox(height: 16),
      _detail(Icons.place_outlined, '办理地点', 'location'),
      _detail(Icons.schedule_rounded, '办公时间', 'office_hours'),
      _detail(Icons.event_outlined, '截止日期', 'deadline'),
      _detail(Icons.route_outlined, '办理方式', 'channel'),
      _detail(Icons.support_agent_rounded, '咨询渠道', 'contact'),
      for (final note in card['notes'] as List? ?? [])
        Container(
          margin: EdgeInsets.only(top: 4, bottom: 8), padding: EdgeInsets.all(12),
          decoration: BoxDecoration(color: Theme.of(context).brightness == Brightness.dark
              ? Color(0xFF342B1C) : Color(0xFFFFF6E6),
              borderRadius: BorderRadius.circular(12)),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(Icons.lightbulb_outline_rounded, size: 16, color: Color(0xFF967536)),
            SizedBox(width: 8),
            Expanded(child: Text(note as String,
                style: TextStyle(fontSize: 12, color: Theme.of(context).brightness == Brightness.dark
                    ? Color(0xFFE6CA90) : Color(0xFF796235)))),
          ]),
        ),
      Padding(padding: EdgeInsets.symmetric(vertical: 10), child: Divider(height: 1)),
      Row(children: [
        Icon(Icons.verified_outlined, size: 15, color: CampusPalette.of(context).green),
        SizedBox(width: 6),
        Text('信息出处', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      ]),
      SizedBox(height: 8),
      for (final source in sources) ...[
        Text(source['title'] as String? ?? '未查到出处',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
        Text((source['issuer'] ?? '').toString() + ' · ' + (source['date'] ?? '').toString(),
            style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted)),
        if (source['url'] is String)
          TextButton.icon(
            style: TextButton.styleFrom(padding: EdgeInsets.zero,
                alignment: Alignment.centerLeft, foregroundColor: CampusPalette.of(context).green),
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: source['url'] as String));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('原文链接已复制')));
              }
            },
            icon: Icon(Icons.link_rounded, size: 16), label: Text('复制原文链接'),
          ),
      ],
      SizedBox(height: 12),
      Wrap(spacing: 8, children: [
        if (widget.onSave != null) TextButton.icon(onPressed: widget.onSave,
            icon: Icon(Icons.bookmark_add_outlined), label: Text('保存到资料夹')),
        if (widget.onReminder != null) TextButton.icon(onPressed: widget.onReminder,
            icon: Icon(Icons.alarm_add_outlined), label: Text('设置提醒')),
      ]),
      Text('材料勾选保存在本机；离线资料可能过期，办理前请核对原文。',
          style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
    ]);
  }

  Widget _detail(IconData icon, String label, String name) => Padding(
    padding: EdgeInsets.only(bottom: 12),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(icon, size: 16, color: CampusPalette.of(context).muted),
      SizedBox(width: 8),
      SizedBox(width: 62, child: Text(label,
          style: TextStyle(fontSize: 12, color: CampusPalette.of(context).muted))),
      Expanded(child: Text(field(name), style: TextStyle(fontSize: 12, height: 1.6))),
    ]),
  );
}
