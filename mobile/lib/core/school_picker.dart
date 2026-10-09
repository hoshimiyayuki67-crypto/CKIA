import 'package:flutter/material.dart';
import 'school.dart';
import 'app_theme.dart';

class SchoolPicker extends StatefulWidget {
  const SchoolPicker({super.key, required this.schools, required this.selected});
  final List<School> schools;
  final String selected;
  @override
  State<SchoolPicker> createState() => _SchoolPickerState();
}

class _SchoolPickerState extends State<SchoolPicker> {
  String _query = '', _province = '';
  @override
  Widget build(BuildContext context) {
    final provinces = widget.schools.map((s) => s.province).where((p) => p.isNotEmpty).toSet().toList()..sort();
    final results = widget.schools.where((s) => (_province.isEmpty || s.province == _province) && s.matches(_query)).toList();
    final palette = CampusPalette.of(context);
    return SafeArea(child: SizedBox(height: MediaQuery.sizeOf(context).height * .82,
      child: Column(children: [
        Padding(padding: const EdgeInsets.fromLTRB(20, 18, 20, 10), child: Row(children: [
          const CampusMark(size: 34), const SizedBox(width: 12),
          Expanded(child: Text('找到你的院校', style: Theme.of(context).textTheme.titleLarge)),
          IconButton(tooltip: '关闭院校选择', onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
        ])),
        Padding(padding: const EdgeInsets.symmetric(horizontal: 20), child: TextField(
          key: const Key('school-search'), onChanged: (value) => setState(() => _query = value.trim()),
          decoration: const InputDecoration(prefixIcon: Icon(Icons.search),
            hintText: '校名、城市、拼音或首字母', labelText: '检索本科院校'))),
        Padding(padding: const EdgeInsets.fromLTRB(20, 12, 20, 8), child: Row(children: [
          Expanded(child: DropdownButtonFormField<String>(initialValue: _province,
            decoration: const InputDecoration(labelText: '省份'),
            items: [const DropdownMenuItem(value: '', child: Text('全国')),
              for (final province in provinces) DropdownMenuItem(value: province, child: Text(province))],
            onChanged: (value) => setState(() => _province = value ?? ''))),
          const SizedBox(width: 12), Text('${results.length} 所', style: TextStyle(color: palette.muted)),
        ])),
        Expanded(child: results.isEmpty ? const Center(child: Text('没有匹配的院校，试试全称或拼音'))
          : ListView.builder(key: const Key('school-results'), itemCount: results.length,
            itemBuilder: (context, index) {
              final school = results[index];
              return ListTile(title: Text(school.name),
                subtitle: Text([school.province, school.city,
                  if (school.domain.isNotEmpty) school.domain].where((v) => v.isNotEmpty).join(' · ')),
                trailing: school.id == widget.selected ? Icon(Icons.check_circle, color: palette.green) : null,
                onTap: () => Navigator.pop(context, school));
            })),
        Padding(padding: const EdgeInsets.fromLTRB(20, 8, 20, 4), child: Text(
          '教育部2026年公开本科名单 · 查询按所选院校隔离',
          style: TextStyle(fontSize: 11, color: palette.muted))),
        TextButton.icon(onPressed: () => Navigator.pop(context, const School('add', '', '')),
          icon: const Icon(Icons.add_circle_outline), label: const Text('添加或指定院校官网')),
      ])));
  }
}
