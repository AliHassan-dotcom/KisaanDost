import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../utils/logger.dart';

abstract interface class SecureStorageService {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
  Future<void> deleteAll();
}

final class FlutterSecureStorageService implements SecureStorageService {
  const FlutterSecureStorageService({
    this._storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(),
      iOptions: IOSOptions(
        accountName: 'kisaan_dost_account',
      ),
    ),
  });

  final FlutterSecureStorage _storage;

  static const String tokenKey = 'access_token';
  static const String languageKey = 'language';

  @override
  Future<String?> read(String key) async {
    try {
      Logger.startup('SecureStorage read initiated', 'key=$key');
      final value = await _storage.read(key: key);
      Logger.startup(
        'SecureStorage read completed',
        'key=$key, found=${value != null && value.isNotEmpty}',
      );
      return value;
    } on Object catch (e, st) {
      Logger.error('SecureStorage read failed for key=$key', error: e, stackTrace: st);
      return null;
    }
  }

  @override
  Future<void> write(String key, String value) async {
    try {
      await _storage.write(key: key, value: value);
    } on Object catch (e, st) {
      Logger.error('SecureStorage write failed for key=$key', error: e, stackTrace: st);
    }
  }

  @override
  Future<void> delete(String key) async {
    try {
      await _storage.delete(key: key);
    } on Object catch (e, st) {
      Logger.error('SecureStorage delete failed for key=$key', error: e, stackTrace: st);
    }
  }

  @override
  Future<void> deleteAll() async {
    try {
      await _storage.deleteAll();
    } on Object catch (e, st) {
      Logger.error('SecureStorage deleteAll failed', error: e, stackTrace: st);
    }
  }
}
