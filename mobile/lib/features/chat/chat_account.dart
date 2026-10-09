// Companion methods operate on the owning State inside the same library.
// ignore_for_file: invalid_use_of_protected_member
part of 'chat_screen.dart';

extension _ChatAccount on _ChatScreenState {
  bool _visibleSession(Json session) => session['owner'] == null ||
      session['owner'] == widget.cloud?.user?['id'];

  Future<void> _restoreAccount() async {
    if (widget.cloud == null) return;
    try { await widget.cloud!.restore(verify: !_offline); }
    catch (_) { _notice('暂时无法连接账号服务，本地记录仍可使用'); }
    if (!mounted) return;
    if (_sessionOwner != null && _sessionOwner != widget.cloud?.user?['id']) {
      setState(() { _messages.clear(); _sessionOwner = null;
        _sessionId = DateTime.now().microsecondsSinceEpoch.toString(); });
    }
    if (_messages.isEmpty) _sessionOwner = widget.cloud?.user?['id'] as String?;
    setState(() {});
    await _syncCloud();
  }

  Future<void> _syncCloud({bool includeLocal = false}) async {
    final cloud = widget.cloud;
    if (cloud == null || !cloud.signedIn || _syncing || _sending || _offline || !_storageHealthy) return;
    final owner = cloud.user!['id'] as String;
    if (!mounted) return;
    setState(() { _syncing = true; _syncStatus = '正在同步'; });
    try {
      await _persist();
      if (includeLocal) {
        for (final session in _sessions.where((s) => s['owner'] == null)) {
          session['owner'] = owner; session['dirty'] = true;
          if (session['id'] == _sessionId) _sessionOwner = owner;
        }
      }
      for (final pending in List<Json>.from(_pendingDeletes).where((s) => s['owner'] == owner)) {
        try { await cloud.deleteSession(pending); }
        on CloudError catch (error) {
          if (![404, 409].contains(error.status)) rethrow;
          if (error.status == 409) _notice('有对话已在其他设备更新，未删除最新云端记录');
        }
        _pendingDeletes.remove(pending);
      }
      final rows = await cloud.sessions();
      for (final row in rows) {
        final matches = _sessions.where((s) => s['id'] == row['id'] && s['owner'] == owner).toList();
        final local = matches.isEmpty ? null : matches.first;
        if (local?['dirty'] == true) {
          if ((local!['cloud_revision'] ?? 0) == row['revision'] && row['deleted'] != true) continue;
          // Preserve a concurrent local edit as a separate conversation instead of overwriting.
          final oldId = local['id'];
          local['id'] = '${DateTime.now().microsecondsSinceEpoch}-copy';
          local['cloud_revision'] = 0;
          if (_sessionId == oldId) _sessionId = local['id'] as String;
          _notice('发现另一台设备的修改，已保留两个对话版本');
        } else if (local != null) { _sessions.remove(local); }
        if (row['deleted'] != true) {
          _sessions.add({...Map<String, dynamic>.from(row['data'] as Map),
            'id': row['id'], 'owner': owner, 'cloud_revision': row['revision'], 'dirty': false});
        } else if (_sessionId == row['id'] && local?['dirty'] != true) {
          _messages.clear(); _sessionId = DateTime.now().microsecondsSinceEpoch.toString();
          _sessionOwner = owner;
        }
      }
      for (final session in _sessions.where((s) => s['owner'] == owner && s['dirty'] == true)) {
        session['cloud_revision'] = await cloud.save(session);
        session['dirty'] = false;
      }
      _sessions.sort((a, b) => (b['updated_at'] as String).compareTo(a['updated_at'] as String));
      final current = _sessions.where((s) => s['id'] == _sessionId && s['owner'] == owner).toList();
      if (current.isNotEmpty) {
        _messages.clear();
        _messages.addAll((current.first['messages'] as List)
            .map((m) => Map<String, dynamic>.from(m as Map)));
        _category = current.first['category'] as String?;
      }
      _syncStatus = '已同步到云端';
    } catch (error) {
      _syncStatus = error is CloudError && error.status == 401 ? '登录已过期' : '待同步 · 本机已保存';
      if (includeLocal || error is CloudError) {
        _notice(error is CloudError ? error.message : '云端连接失败，记录已保留在本机');
      }
    } finally {
      if (mounted) {
        setState(() => _syncing = false);
        await _persist();
      }
    }
  }

  Future<void> _forgetAccount(String owner) async {
    setState(() {
      _sessions.removeWhere((s) => s['owner'] == owner);
      _pendingDeletes.removeWhere((s) => s['owner'] == owner);
      if (_sessionOwner == owner) { _messages.clear(); _sessionOwner = null;
        _sessionId = DateTime.now().microsecondsSinceEpoch.toString(); }
      _syncStatus = '本机保存';
    });
    await _persist(); await _persist();
  }

  Future<void> _account() async {
    final cloud = widget.cloud;
    if (cloud == null) { _notice('请使用连接在线服务的安卓版本'); return; }
    final username = TextEditingController(), password = TextEditingController();
    var register = false, busy = false, hidden = true;
    String? error;
    if (!mounted) return;
    await showModalBottomSheet<void>(context: context, isScrollControlled: true,
      showDragHandle: true, builder: (sheetContext) => StatefulBuilder(builder: (sheetContext, update) {
        Future<void> action(Future<void> Function() task) async {
          if (busy) return;
          update(() { busy = true; error = null; });
          try { await task(); }
          catch (failure) {
            if (sheetContext.mounted) update(() => error = failure is CloudError
                ? failure.message : '连接失败，请稍后重试');
          } finally {
            if (sheetContext.mounted) update(() => busy = false);
            if (mounted) setState(() {});
          }
        }
        return PopScope(canPop: !busy, child: Padding(
          padding: EdgeInsets.fromLTRB(24, 0, 24, MediaQuery.viewInsetsOf(sheetContext).bottom + 24),
          child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const Icon(Icons.cloud_done_outlined, size: 38, color: CampusColors.green),
              const SizedBox(height: 12),
              Text(cloud.signedIn ? cloud.user!['username'] as String : '把对话带在身边',
                textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(cloud.signedIn ? _syncStatus : '登录后，新对话自动保存到云端，换手机也能继续。',
                textAlign: TextAlign.center, style: const TextStyle(color: CampusColors.muted, fontSize: 12)),
              const SizedBox(height: 20),
              if (!cloud.signedIn) ...[
                TextField(key: const Key('account-username'), controller: username, enabled: !busy,
                  maxLength: 32, autofillHints: const [AutofillHints.username],
                  decoration: const InputDecoration(labelText: '用户名', helperText: '3–32位字母、数字或下划线')),
                TextField(key: const Key('account-password'), controller: password, enabled: !busy,
                  obscureText: hidden, maxLength: 128,
                  decoration: InputDecoration(labelText: '密码', helperText: '至少8位，请记住密码',
                    suffixIcon: IconButton(onPressed: () => update(() => hidden = !hidden),
                      icon: Icon(hidden ? Icons.visibility_outlined : Icons.visibility_off_outlined)))),
                const SizedBox(height: 8),
                FilledButton(onPressed: busy ? null : () => action(() async {
                  if (!RegExp(r'^[a-zA-Z0-9_]{3,32}$').hasMatch(username.text.trim()) || password.text.length < 8) {
                    throw const CloudError(422, '请检查用户名格式，密码至少8位');
                  }
                  await cloud.authenticate(username.text, password.text, register: register);
                  _newChat();
                  await _syncCloud();
                }), child: Text(register ? '创建账号' : '登录')),
                TextButton(onPressed: busy ? null : () => update(() { register = !register; error = null; }),
                  child: Text(register ? '已有账号？登录' : '没有账号？注册')),
                const Text('仅同步聊天文字与回答。图片、提醒和资料夹仍保存在本机。暂不提供密码找回。',
                  style: TextStyle(fontSize: 11, color: CampusColors.muted)),
              ] else ...[
                FilledButton.icon(onPressed: busy || _offline ? null : () => action(() => _syncCloud()),
                  icon: const Icon(Icons.sync), label: const Text('同步云端聊天')),
                OutlinedButton.icon(onPressed: busy || _offline ? null : () => action(() async {
                  final yes = await showDialog<bool>(context: sheetContext, builder: (ctx) => AlertDialog(
                    title: const Text('导入本机聊天？'),
                    content: const Text('将未关联账号的本机聊天上传到当前账号，最多保留50个云端对话。'),
                    actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
                      FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('导入'))]));
                  if (yes == true) await _syncCloud(includeLocal: true);
                }), icon: const Icon(Icons.cloud_upload_outlined), label: const Text('导入本机历史')),
                TextButton(onPressed: busy ? null : () => action(() async {
                  final owner = cloud.user!['id'] as String;
                  try { await cloud.logout(); } finally {
                    if (!cloud.signedIn && mounted) await _forgetAccount(owner);
                  }
                }), child: const Text('退出登录')),
                TextButton(onPressed: busy ? null : () => action(() async {
                  final owner = cloud.user!['id'] as String;
                  final confirmation = TextEditingController();
                  final yes = await showDialog<bool>(context: sheetContext, builder: (ctx) => AlertDialog(
                    title: const Text('删除账号与云端记录？'),
                    content: Column(mainAxisSize: MainAxisSize.min, children: [
                      const Text('此操作永久删除账号及全部云端聊天。请输入密码确认。'),
                      TextField(controller: confirmation, obscureText: true, maxLength: 128,
                        decoration: const InputDecoration(labelText: '密码'))]),
                    actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
                      FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('永久删除'))]));
                  final value = confirmation.text;
                  await Future<void>.delayed(const Duration(milliseconds: 250)); confirmation.dispose();
                  if (yes == true) { await cloud.deleteAccount(value); if (mounted) await _forgetAccount(owner); }
                }), child: const Text('删除账号', style: TextStyle(color: Colors.red))),
              ],
              if (busy) const Padding(padding: EdgeInsets.all(12),
                child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)))),
              if (error != null) Text(error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
              const Divider(height: 28),
              const Text('校园万事通 0.5.0 · 官网资料由 AI 整理，请核对现行要求。',
                style: TextStyle(fontSize: 11, color: CampusColors.muted)),
            ])),
        ));
      }));
    await Future<void>.delayed(const Duration(milliseconds: 250)); username.dispose(); password.dispose();
  }

  Future<void> _deleteConversation(Json session) async {
    if (session['owner'] != null && (session['cloud_revision'] as int? ?? 0) > 0) {
      _pendingDeletes.add({'id': session['id'], 'owner': session['owner'],
        'cloud_revision': session['cloud_revision']});
    }
    setState(() {
      _sessions.remove(session);
      if (_sessionId == session['id']) {
        _messages.clear(); _sessionId = DateTime.now().microsecondsSinceEpoch.toString();
        _sessionOwner = widget.cloud?.user?['id'] as String?;
      }
    });
    await _persist(); await _syncCloud();
  }
}
