import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'reply_service.dart';

abstract class LocalStore {
  Future<Json> read();
  Future<void> write(Json data);
}

class MemoryStore implements LocalStore {
  Json data = {};
  @override
  Future<Json> read() async => jsonDecode(jsonEncode(data)) as Json;
  @override
  Future<void> write(Json value) async { data = jsonDecode(jsonEncode(value)) as Json; }
}

class FileStore implements LocalStore {
  FileStore({this.directory});
  final Future<Directory> Function()? directory;
  Future<void> _pending = Future.value();
  bool _preserveBackup = false;
  Future<File> _file() async {
    final dir = await (directory?.call() ?? getApplicationSupportDirectory());
    await dir.create(recursive: true);
    return File('${dir.path}/campus-state.json');
  }

  @override
  Future<Json> read() async {
    final file = await _file();
    for (final path in [file.path, '${file.path}.bak']) {
      try {
        final candidate = File(path);
        if (await candidate.exists()) {
          final data = jsonDecode(await candidate.readAsString()) as Json;
          if (data['version'] != 1) throw const FormatException('不支持的本地数据版本');
          _preserveBackup = path != file.path;
          return data;
        }
      } on FormatException { continue; }
    }
    if (await file.exists() || await File('${file.path}.bak').exists()) {
      throw const FormatException('本地记录损坏，未覆盖原文件');
    }
    return {};
  }

  @override
  Future<void> write(Json data) {
    final text = jsonEncode({...data, 'version': 1});
    final next = _pending.then((_) async {
      final file = await _file();
      final temp = File('${file.path}.tmp');
      await temp.writeAsString(text, flush: true);
      if (!_preserveBackup && await file.exists()) await file.copy('${file.path}.bak');
      await temp.rename(file.path);
      _preserveBackup = false;
    });
    _pending = next.catchError((Object _) {});
    return next;
  }
}
