import 'dart:convert';
import 'dart:io';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'reply_service.dart';

class CloudError implements Exception {
  const CloudError(this.status, this.message);
  final int status;
  final String message;
}

abstract class CredentialStore {
  Future<String?> read();
  Future<void> write(String? value);
}

class SecureCredentials implements CredentialStore {
  SecureCredentials(this.server);
  final String server;
  final _storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(encryptedSharedPreferences: true));
  String get _key => 'campus-account-$server';
  @override
  Future<String?> read() => _storage.read(key: _key);
  @override
  Future<void> write(String? value) => value == null
      ? _storage.delete(key: _key) : _storage.write(key: _key, value: value);
}

typedef CloudTransport = Future<Json> Function(
    String method, String path, Json? body, String? token);

class CloudClient {
  CloudClient(this.baseUrl, {required this.credentials, this.transport});
  final String baseUrl;
  final CredentialStore credentials;
  final CloudTransport? transport;
  String? _token;
  Json? user;
  bool get signedIn => user != null && _token != null;

  Future<Json> _request(String method, String path, [Json? body]) async {
    if (transport != null) return transport!(method, path, body, _token);
    final base = Uri.parse(baseUrl);
    if (base.scheme != 'https' || base.host.isEmpty) {
      throw const CloudError(0, '账号服务需要 HTTPS 地址');
    }
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 8);
    try {
      final request = await client.openUrl(method,
          Uri.parse('${baseUrl.replaceFirst(RegExp(r'/+$'), '')}/api/v1$path'));
      request.headers.contentType = ContentType.json;
      if (_token != null) request.headers.set('Authorization', 'Bearer $_token');
      if (body != null) request.write(jsonEncode(body));
      final response = await request.close().timeout(const Duration(seconds: 20));
      final bytes = <int>[];
      await for (final chunk in response.timeout(const Duration(seconds: 20))) {
        bytes.addAll(chunk);
        if (bytes.length > 11000000) throw const CloudError(0, '云端响应过大');
      }
      final value = jsonDecode(utf8.decode(bytes)) as Json;
      if (response.statusCode >= 400) {
        throw CloudError(response.statusCode,
            value['detail'] is String ? value['detail'] as String : '请求不正确，请检查输入');
      }
      return value;
    } finally { client.close(force: true); }
  }

  Future<void> restore({bool verify = true}) async {
    final raw = await credentials.read();
    if (raw == null) return;
    final saved = jsonDecode(raw) as Json;
    _token = saved['token'] as String;
    user = Map<String, dynamic>.from(saved['user'] as Map);
    if (!verify) return;
    try { user = await _request('GET', '/auth/me'); }
    on CloudError catch (error) {
      if (error.status == 401) { await _clear(); return; }
      rethrow;
    }
  }

  Future<void> authenticate(String username, String password, {bool register = false}) async {
    final result = await _request('POST', register ? '/auth/register' : '/auth/login',
        {'username': username.trim(), 'password': password});
    // Commit secure storage before considering login complete.
    await credentials.write(jsonEncode(result));
    _token = result['token'] as String;
    user = Map<String, dynamic>.from(result['user'] as Map);
  }

  Future<void> _clear() async {
    await credentials.write(null);
    _token = null; user = null;
  }

  Future<void> logout() async {
    try { await _request('POST', '/auth/logout'); }
    finally { await _clear(); }
  }

  Future<void> deleteAccount(String password) async {
    await _request('DELETE', '/auth/account', {'password': password});
    await _clear();
  }

  Future<List<Json>> sessions() async {
    final data = await _request('GET', '/sessions');
    return (data['sessions'] as List)
        .map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<int> save(Json session) async {
    final result = await _request('PUT', '/sessions/${session['id']}', {
      'revision': session['cloud_revision'] ?? 0,
      'data': {for (final key in ['title', 'school', 'category', 'updated_at', 'messages'])
        key: session[key]},
    });
    return result['revision'] as int;
  }

  Future<void> deleteSession(Json session) async {
    await _request('DELETE', '/sessions/${session['id']}?revision=${session['cloud_revision'] ?? 0}');
  }
}
