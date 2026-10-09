// Companion methods operate on the owning State inside the same library.
// ignore_for_file: invalid_use_of_protected_member
part of 'chat_screen.dart';

extension _ChatTools on _ChatScreenState {
  void _notice(String text) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _restore() async {
    try {
      final catalogue = await loadSchoolCatalogue();
      final data = await widget.store?.read() ?? <String, dynamic>{};
      if (!mounted) return;
      setState(() {
        _catalogue.addAll(catalogue);
        _customSchools.addAll((data['custom_schools'] as List? ?? [])
            .map((value) => School.fromJson(Map<String, dynamic>.from(value as Map))));
        final all = [..._catalogue, ..._customSchools];
        _school = all.firstWhere((value) => value.id == data['school_id'], orElse: () => schools.first);
        _searchEnabled = data['search_enabled'] == true;
        _offline = data['offline'] == true;
        _themePreference = data['theme'] as String? ?? 'system';
        _sessionId = data['current_session'] as String? ?? _sessionId;
        for (final pair in (data['checks'] as Map? ?? {}).entries) {
          _checks[pair.key as String] = (pair.value as List).cast<int>();
        }
        for (final pair in {'sessions': _sessions, 'saved': _saved, 'reminders': _reminders}.entries) {
          pair.value.addAll((data[pair.key] as List? ?? [])
              .map((value) => Map<String, dynamic>.from(value as Map)));
        }
        _pendingDeletes.addAll((data['pending_deletes'] as List? ?? [])
            .map((value) => Map<String, dynamic>.from(value as Map)));
        for (final session in _sessions) {
          if (session['id'] == _sessionId) {
            _messages.addAll((session['messages'] as List)
                .map((value) => Map<String, dynamic>.from(value as Map)));
            _category = session['category'] as String?;
            _sessionOwner = session['owner'] as String?;
          }
        }
      });
      widget.onThemeChanged?.call(ThemeMode.values.firstWhere((mode) => mode.name == _themePreference,
          orElse: () => ThemeMode.system));
      _scrollToEnd();
    } catch (_) {
      if (!mounted) return;
      setState(() { _loading = false; _storageHealthy = false; });
      _notice('本地记录无法读取，已停止覆盖原文件。请在资料页清除损坏的数据后重试。');
    }
    if (widget.device != null) {
      try {
        final recovered = await widget.device!.recoverPhoto();
        if (recovered != null && mounted) await _reviewText(recovered);
      } catch (_) { _notice('上次图片未能恢复，请重新选择图片'); }
    }
    await _restoreAccount();
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _persist() async {
    if (!_storageHealthy || widget.store == null) return;
    final prior = _sessions.where((value) => value['id'] == _sessionId).toList();
    final previous = prior.isEmpty ? <String, dynamic>{} : prior.first;
    _sessions.removeWhere((value) => value['id'] == _sessionId);
    if (_messages.isNotEmpty) {
      // Keep complete conversation pairs; cap retained history to 20 conversations.
      if (_messages.length > 100) _messages.removeRange(0, _messages.length - 100);
      final changed = jsonEncode(previous['messages']) != jsonEncode(_messages) || previous['category'] != _category;
      final title = _messages.first['message'] as String? ?? '校园对话';
      _sessions.insert(0, {'id': _sessionId, 'school': _school.toJson(),
        'title': title.length > 200 ? title.substring(0, 200) : title, 'category': _category,
        'owner': _sessionOwner, 'cloud_revision': previous['cloud_revision'] ?? 0,
        'dirty': previous['dirty'] == true || changed,
        'updated_at': changed ? DateTime.now().toIso8601String() : previous['updated_at'],
        'messages': List<Json>.from(_messages)});
    }
    for (var i = _sessions.length - 1; i >= 20; i--) {
      final session = _sessions[i];
      if (session['id'] != _sessionId && !(session['owner'] != null && session['dirty'] == true)) {
        _sessions.removeAt(i);
      }
    }
    final liveCards = [..._saved, ..._sessions.expand((session) =>
        (session['messages'] as List).map((item) => Map<String, dynamic>.from(item as Map)))];
    final liveKeys = liveCards.where((item) => item['card'] is Map).map(_cardKey).toSet();
    _checks.removeWhere((key, _) => !liveKeys.contains(key));
    try {
      await widget.store!.write({'version': 1, 'current_session': _sessionId,
        'school_id': _school.id, 'custom_schools': _customSchools.map((value) => value.toJson()).toList(),
        'search_enabled': _searchEnabled, 'offline': _offline,
        'theme': _themePreference,
        'sessions': _sessions, 'saved': _saved, 'checks': _checks, 'reminders': _reminders,
        'pending_deletes': _pendingDeletes});
    } catch (_) { _notice('保存失败，请检查手机存储空间；本次内容仍可在页面查看'); }
  }

  Widget _queryControls() => Padding(
    padding: EdgeInsets.symmetric(horizontal: 16),
    child: Column(children: [
      Row(children: [
        Icon(Icons.school_outlined, size: 17, color: CampusPalette.of(context).green),
        SizedBox(width: 5),
        Expanded(child: TextButton(onPressed: _sending || _loading || _syncing ? null : _selectSchool,
          style: TextButton.styleFrom(alignment: Alignment.centerLeft),
          child: Text(_school.name, overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12)))),
        Icon(Icons.expand_more, size: 16),
        PopupMenuButton<ThemeMode>(tooltip: '外观模式',
          icon: Icon(Icons.contrast_rounded, size: 20),
          onSelected: (mode) {
            setState(() => _themePreference = mode.name);
            widget.onThemeChanged?.call(mode); _persist();
          }, itemBuilder: (context) => [
            for (final mode in ThemeMode.values) CheckedPopupMenuItem(value: mode,
              checked: widget.themeMode == mode,
              child: Text(switch(mode) {ThemeMode.system => '跟随系统', ThemeMode.light => '浅色模式', ThemeMode.dark => '暗黑模式'})),
          ]),
      ]),
      if (widget.cloud?.signedIn == true) Padding(
        padding: EdgeInsets.only(bottom: 4), child: Row(children: [
          Icon(_syncing ? Icons.sync : Icons.cloud_done_outlined, size: 13, color: CampusPalette.of(context).muted),
          SizedBox(width: 5),
          Text(_syncStatus, style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
        ])),
      Row(children: [
        Expanded(child: Row(children: [
          Icon(Icons.travel_explore, size: 17, color: CampusPalette.of(context).muted),
          SizedBox(width: 5),
          Text('联网搜索', style: TextStyle(fontSize: 11)),
          Transform.scale(scale: .8, child: Switch(key: Key('search-switch'),
            value: _searchEnabled && !_offline,
            onChanged: _sending || _syncing || _offline || widget.service.demoMode ? null : (value) {
              setState(() => _searchEnabled = value); _persist();
            })),
        ])),
        Text('离线资料', style: TextStyle(fontSize: 11)),
        Transform.scale(scale: .8, child: Switch(key: Key('offline-switch'), value: _offline,
          onChanged: _sending || _syncing ? null : (value) {
            setState(() => _offline = value); _persist();
          })),
      ]),
    ]),
  );

  Future<void> _selectSchool() async {
    final selected = await showModalBottomSheet<School>(context: context, isScrollControlled: true,
      builder: (context) => SchoolPicker(schools: [...(_catalogue.isEmpty ? schools : _catalogue), ..._customSchools], selected: _school.id));
    if (selected?.id == 'add') { if (mounted) await _addSchool(); return; }
    if (selected != null && mounted && selected.id != _school.id) {
      _newChat();
      setState(() => _school = selected);
      await _persist();
    }
  }

  Future<void> _addSchool() async {
    final name = TextEditingController(), domain = TextEditingController();
    String? error;
    final school = await showDialog<School>(context: context, builder: (context) =>
      StatefulBuilder(builder: (context, update) => AlertDialog(title: Text('添加院校'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: name, maxLength: 100, decoration: InputDecoration(labelText: '院校全称')),
          TextField(controller: domain, maxLength: 253,
            decoration: InputDecoration(labelText: '官网域名', hintText: 'example.edu.cn')),
          Text('自定义域名由你提供，请确认官网归属。不会自动导入为审核知识库。',
              style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted)),
          if (error != null) Text(error!, style: TextStyle(color: Colors.red)),
        ])), actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text('取消')),
          FilledButton(onPressed: () {
            final host = domain.text.trim().toLowerCase().replaceFirst(RegExp(r'^www\.'), '');
            if (name.text.trim().length < 2 || !RegExp(r'^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$').hasMatch(host)
                || host.contains('..')) {
              update(() => error = '请输入院校名称和有效官网域名'); return;
            }
            Navigator.pop(context, School('custom-$host', name.text.trim(), host));
          }, child: Text('添加'))])));
    // Dialog route completes its closing animation before controllers are released.
    await Future<void>.delayed(Duration(milliseconds: 250));
    name.dispose(); domain.dispose();
    if (school != null && mounted) {
      _newChat();
      setState(() {
        _customSchools.removeWhere((value) => value.id == school.id);
        _customSchools.add(school); _school = school;
      });
      await _persist();
    }
  }

  String _cardKey(Json item) {
    final card = Map<String, dynamic>.from(item['card'] as Map);
    final source = (card['sources'] as List? ?? []).map((value) => '${value['doc_id']}:${value['chunk_id']}').join('|');
    return '${item['school_id'] ?? _school.id}|${card['matter_name']}|$source';
  }

  Widget _card(Json item) {
    final key = _cardKey(item);
    return ActionCardView(key: ValueKey(key), card: Map<String, dynamic>.from(item['card'] as Map),
      checked: _checks[key] ?? [], onChecked: (value) {
        setState(() => _checks[key] = value); _persist();
      }, onSave: () {
        setState(() {
          _saved.removeWhere((value) => _cardKey(value) == key);
          _saved.insert(0, {...item, 'school': _school.toJson(), 'saved_at': DateTime.now().toIso8601String()});
          if (_saved.length > 100) _saved.removeLast();
        });
        _persist(); _notice('已保存，可在本地资料页离线查看');
      }, onReminder: () => _addReminder(item['card']['matter_name'] as String));
  }

  Widget _webSource(Json source) => Padding(padding: EdgeInsets.only(top: 12),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(source['historical'] == true ? '本地学生手册 · 历史版本'
          : source['verified'] == true ? '本地审核资料' : '${source['id']} · 官网搜索摘要 · 未审核',
          style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
      Text(source['title'] as String? ?? '', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
      Text(source['snippet'] as String? ?? '', style: TextStyle(fontSize: 12, height: 1.6)),
      Text('${source['verified'] == true ? '发布于' : '检索于'} ${source['retrieved_at'] ?? ''}',
          style: TextStyle(fontSize: 10, color: CampusPalette.of(context).muted)),
      Wrap(children: [
        TextButton.icon(onPressed: () async {
          final uri = Uri.tryParse(_sourceUrl(source));
          try {
            if (uri == null || !['https', 'http'].contains(uri.scheme) ||
                !await launchUrl(uri, mode: LaunchMode.externalApplication)) _notice('无法打开链接');
          } catch (_) { _notice('无法打开链接，可复制后使用浏览器查看'); }
        }, icon: Icon(Icons.open_in_new, size: 15), label: Text('查看原文')),
        TextButton(onPressed: () async {
          await Clipboard.setData(ClipboardData(text: _sourceUrl(source)));
          _notice('链接已复制');
        }, child: Text('复制链接')),
      ]),
    ]));

  String _sourceUrl(Json source) {
    final url = source['url'] as String? ?? '';
    if (url.startsWith('/') && widget.service is ApiReplyService) {
      return Uri.parse((widget.service as ApiReplyService).baseUrl).resolve(url).toString();
    }
    return url;
  }

  Widget _answerDetails(Json item) {
    final web = (item['web_sources'] as List? ?? [])
        .map((s) => Map<String, dynamic>.from(s as Map)).toList();
    final local = (item['local_evidence'] as Map? ?? {}).entries.map((entry) =>
      {...Map<String, dynamic>.from(entry.value as Map), 'id': entry.key,
        'verified': true, 'historical': entry.value['doc_id'] == 'imuchuangye-handbook-2021',
        'snippet': '', 'retrieved_at': entry.value['date_precision'] == 'month'
            ? (entry.value['date'] as String).substring(0, 7) : entry.value['date']}).toList();
    final sources = [...web, ...local];
    final points = item['summary_points'] as List? ?? [];
    final legacy = item['analysis'] as List? ?? [];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      for (final point in points) Padding(padding: EdgeInsets.only(top: 18),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Container(width: 3, height: 16, decoration: BoxDecoration(
            color: CampusPalette.of(context).green, borderRadius: BorderRadius.circular(3))),
            SizedBox(width: 8), Text(point['heading'] as String,
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700))]),
          SizedBox(height: 8),
          SelectableText(point['text'] as String, style: TextStyle(fontSize: 14, height: 1.8)),
          Wrap(spacing: 6, children: [
            for (final ref in (point['support'] as List? ?? [])
                .map((s) => s['reference'] as String).toSet())
              TextButton.icon(style: TextButton.styleFrom(visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.symmetric(horizontal: 8)),
                onPressed: () {
                  final matches = sources.where((s) => s['id'] == ref).toList();
                  if (matches.isNotEmpty) _showPage('原文依据', [_webSource(matches.first),
                    for (final support in point['support'] as List)
                      if (support['reference'] == ref) Padding(padding: EdgeInsets.only(top: 12),
                        child: SelectableText('原文：${support['quote']}', style: TextStyle(fontSize: 13)))]);
                }, icon: Icon(Icons.link_rounded, size: 13),
                label: Text('依据 ${sources.indexWhere((s) => s['id'] == ref) + 1}',
                  style: TextStyle(fontSize: 10))),
          ]),
        ])),
      if (sources.isNotEmpty || legacy.isNotEmpty) ExpansionTile(
        title: Text('查看 ${sources.length} 份来源与原文',
          style: TextStyle(fontSize: 12, color: CampusPalette.of(context).muted)),
        leading: Icon(Icons.library_books_outlined, size: 17, color: CampusPalette.of(context).muted),
        children: [
          for (final claim in legacy) Padding(padding: EdgeInsets.only(top: 8),
            child: Text(claim['text'] as String, style: TextStyle(fontSize: 12))),
          for (final source in sources) _webSource(source),
        ],
      ),
    ]);
  }

  Future<void> _photo() async {
    final camera = await showModalBottomSheet<bool>(context: context, builder: (context) =>
      SafeArea(child: Column(mainAxisSize: MainAxisSize.min, children: [
        ListTile(title: Text('识别通知或材料文字'), subtitle: Text('在手机端识别，照片不上传。发送前请删除个人信息。')),
        ListTile(leading: Icon(Icons.camera_alt_outlined), title: Text('拍照'), onTap: () => Navigator.pop(context, true)),
        ListTile(leading: Icon(Icons.photo_library_outlined), title: Text('选择图片'), onTap: () => Navigator.pop(context, false)),
      ])));
    if (camera == null || !mounted) return;
    if (widget.device == null) { _notice('请在安卓 APK 中使用图片识别'); return; }
    setState(() => _recognizing = true);
    try {
      final text = await widget.device!.recognize(camera: camera);
      if (mounted) setState(() => _recognizing = false);
      if (mounted && text != null) await _reviewText(text);
    } catch (_) { _notice('识别失败，请检查相机权限或选择更清晰的图片'); }
    finally { if (mounted) setState(() => _recognizing = false); }
  }

  Future<void> _reviewText(String text) async {
    if (text.trim().isEmpty) { _notice('未识别到文字，请重拍清晰的文字区域'); return; }
    final editor = TextEditingController(text: text.length > 2000 ? text.substring(0, 2000) : text);
    final result = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: Text('核对识别文字'),
      content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text('识别可能有误，请修改并删除姓名、学号等个人信息。确认后填入输入框，不会自动发送。', style: TextStyle(fontSize: 12)),
        TextField(controller: editor, minLines: 4, maxLines: 10, maxLength: 2000),
      ])), actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text('取消')),
        FilledButton(onPressed: () => Navigator.pop(context, editor.text), child: Text('填入问题'))]));
    await Future<void>.delayed(Duration(milliseconds: 250)); editor.dispose();
    if (result != null && mounted) setState(() => _input.text = result);
  }

  void _findOffline(String question) {
    final records = [..._saved, ..._sessions.where((value) => _visibleSession(value) && value['school']['id'] == _school.id)
        .expand((value) => (value['messages'] as List).map((item) => Map<String, dynamic>.from(item as Map)))];
    final terms = question.toLowerCase().split(RegExp(r'\s+')).where((value) => value.isNotEmpty);
    final seen = <String>{};
    final hits = records.where((value) => value['user'] != true && value['school_id'] == _school.id &&
        terms.every((term) => '${value['message']} ${value['card'] ?? ''} ${value['summary_points'] ?? ''}'.toLowerCase().contains(term)) &&
        seen.add(value['card'] is Map ? _cardKey(value) : '${value['saved_at']}|${value['message']}'))
        .take(10).toList();
    _showPage('离线查询结果', hits.isEmpty ? [Text('未找到已保存的匹配内容。可输入事项关键词，或关闭离线模式查询最新资料。')]
        : [Text('仅查询本机已保存的内容，可能过期，不代表现行学校规定。'),
          for (final hit in hits) _savedItem(hit)]);
  }

  Widget _savedItem(Json item) => Card(child: Padding(padding: EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('保存于 ${item['saved_at'] ?? '历史记录'}', style: TextStyle(fontSize: 11, color: CampusPalette.of(context).muted)),
      Text(item['message'] as String? ?? ''),
      if (item['card'] is Map) _card(item),
      _answerDetails(item),
    ])));

  void _showPage(String title, List<Widget> children) {
    Navigator.push(context, MaterialPageRoute<void>(builder: (context) => Scaffold(
      appBar: AppBar(title: Text(title)), body: SafeArea(child: ListView(
        padding: EdgeInsets.all(16), children: children)))));
  }

  Future<void> _addReminder([String? suggested]) async {
    if (_reminders.length >= 100) { _notice('提醒最多保留100条，请先删除已完成提醒'); return; }
    final title = TextEditingController(text: suggested ?? '');
    DateTime? when;
    final confirmed = await showDialog<bool>(context: context, builder: (context) =>
      StatefulBuilder(builder: (context, update) => AlertDialog(title: Text('设置办事提醒'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: title, maxLength: 100, decoration: InputDecoration(labelText: '提醒事项')),
          TextButton.icon(icon: Icon(Icons.schedule), label: Text(when?.toString().substring(0, 16) ?? '选择日期和时间'),
            onPressed: () async {
              final now = DateTime.now();
              final day = await showDatePicker(context: context, initialDate: now.add(Duration(days: 1)),
                  firstDate: now, lastDate: now.add(Duration(days: 730)));
              if (day == null || !context.mounted) return;
              final time = await showTimePicker(context: context, initialTime: TimeOfDay(hour: 9, minute: 0));
              if (time != null && context.mounted) update(() => when = DateTime(day.year, day.month, day.day, time.hour, time.minute));
            }),
          Text('手机本地通知，省电设置可能导致延迟。请为重要期限保留其他提醒方式。', style: TextStyle(fontSize: 11)),
        ]), actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text('取消')),
          FilledButton(onPressed: () {
            if (title.text.trim().isEmpty || when == null || !when!.isAfter(DateTime.now())) {
              _notice('请输入事项并选择未来时间'); return;
            }
            Navigator.pop(context, true);
          }, child: Text('保存'))])));
    final text = title.text.trim();
    await Future<void>.delayed(Duration(milliseconds: 250)); title.dispose();
    if (confirmed != true || !mounted) return;
    if (widget.device == null) { _notice('请在安卓 APK 中设置系统提醒'); return; }
    final id = DateTime.now().millisecondsSinceEpoch % 2147483647;
    try {
      await widget.device!.schedule(id, text, when!);
      if (!mounted) return;
      setState(() => _reminders.insert(0, {'id': id, 'title': text,
          'date': when!.toIso8601String(), 'school_id': _school.id}));
      await _persist(); _notice('本地提醒已设置');
    } catch (error) { _notice(error is StateError ? error.message.toString() : '提醒设置失败，请检查系统通知权限'); }
  }

  Future<void> _library() async {
    await _persist();
    if (!mounted) return;
    await Navigator.push(context, MaterialPageRoute<void>(builder: (pageContext) =>
      StatefulBuilder(builder: (pageContext, update) => Scaffold(
        appBar: AppBar(title: Text('本地资料与提醒'), actions: [IconButton(
          tooltip: '清除本地数据', icon: Icon(Icons.delete_sweep_outlined), onPressed: () async {
            final confirmed = await showDialog<bool>(context: pageContext, builder: (context) => AlertDialog(
              title: Text('清除本机数据？'), content: Text('删除聊天记录、保存资料、材料勾选、院校设置，并取消已设置提醒。'),
              actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: Text('取消')),
                FilledButton(onPressed: () => Navigator.pop(context, true), child: Text('清除'))]));
            if (confirmed != true) return;
            try {
              for (final reminder in _reminders) { await widget.device?.cancel(reminder['id'] as int); }
            } catch (_) { _notice('提醒取消失败，未清除数据，请检查系统权限后重试'); return; }
            if (!mounted || !pageContext.mounted) return;
            setState(() {
              _messages.clear(); _sessions.clear(); _saved.clear(); _checks.clear(); _reminders.clear();
              _customSchools.clear(); _school = schools.first; _searchEnabled = false; _offline = false;
              _storageHealthy = true; _sessionId = DateTime.now().microsecondsSinceEpoch.toString();
            });
            await _persist();
            // Second write replaces the previous-data backup with the cleared state as well.
            await _persist();
            if (pageContext.mounted) Navigator.pop(pageContext);
          })]),
        body: SafeArea(child: ListView(padding: EdgeInsets.all(16), children: [
          Text(_school.name, style: Theme.of(context).textTheme.titleMedium),
          Text('本机保留最近20个对话，每个100条消息。登录后的新聊天自动同步；资料夹与提醒仍保存在本机。', style: TextStyle(fontSize: 12)),
          SizedBox(height: 20),
          Text('保存的资料', style: TextStyle(fontWeight: FontWeight.bold)),
          if (!_saved.any((value) => value['school_id'] == _school.id)) ListTile(title: Text('尚未保存资料')),
          for (final item in _saved.where((value) => value['school_id'] == _school.id)) ListTile(
            leading: Icon(Icons.bookmark_outline), title: Text(item['card']['matter_name'] as String),
            subtitle: Text(item['saved_at'] as String? ?? ''), onTap: () => _showPage('已保存资料', [_savedItem(item)]),
            trailing: IconButton(tooltip: '删除资料', icon: Icon(Icons.delete_outline), onPressed: () {
              setState(() => _saved.remove(item)); update(() {}); _persist();
            })),
          SizedBox(height: 16), Text('历史对话', style: TextStyle(fontWeight: FontWeight.bold)),
          for (final session in _sessions.where((value) => _visibleSession(value) && value['school']['id'] == _school.id)) ListTile(
            title: Text(session['title'] as String, maxLines: 2, overflow: TextOverflow.ellipsis),
            subtitle: Text(session['updated_at'] as String), onTap: () {
              setState(() {
                _sessionId = session['id'] as String; _category = session['category'] as String?;
                _sessionOwner = session['owner'] as String?;
                _messages.clear(); _messages.addAll((session['messages'] as List)
                    .map((item) => Map<String, dynamic>.from(item as Map)));
              });
              _persist(); Navigator.pop(pageContext); _scrollToEnd();
            }, trailing: IconButton(tooltip: '删除对话', icon: Icon(Icons.delete_outline), onPressed: () async {
              final confirmed = await showDialog<bool>(context: pageContext, builder: (ctx) => AlertDialog(
                title: Text('删除对话？'), content: Text(session['owner'] == null
                    ? '删除这条本机聊天记录。' : '删除这条聊天，并在同步时删除对应云端记录。'),
                actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text('取消')),
                  FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text('删除'))]));
              if (confirmed != true || !mounted) return;
              await _deleteConversation(session);
              if (pageContext.mounted) update(() {});
            })),
          SizedBox(height: 16), Row(children: [
            Expanded(child: Text('办事提醒', style: TextStyle(fontWeight: FontWeight.bold))),
            TextButton.icon(onPressed: () async { await _addReminder(); if (pageContext.mounted) update(() {}); },
              icon: Icon(Icons.add), label: Text('新增')),
          ]),
          for (final reminder in _reminders.where((value) => value['school_id'] == _school.id)) ListTile(
            title: Text(reminder['title'] as String), subtitle: Text(reminder['date'] as String),
            trailing: IconButton(tooltip: '取消提醒', icon: Icon(Icons.delete_outline), onPressed: () async {
              try { await widget.device?.cancel(reminder['id'] as int); }
              catch (_) { _notice('取消失败，请稍后重试'); return; }
              if (!mounted || !pageContext.mounted) return;
              setState(() => _reminders.remove(reminder)); update(() {}); _persist();
            })),
        ]))))));
  }
}
