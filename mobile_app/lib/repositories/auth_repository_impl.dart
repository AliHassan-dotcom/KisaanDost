import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/user.dart';
import '../services/http_client.dart';
import '../services/secure_storage_service.dart';
import '../utils/error_mapper.dart';
import '../utils/logger.dart';
import 'auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl({
    required this._client,
    required this._secureStorage,
  });

  final HttpClient _client;
  final SecureStorageService _secureStorage;

  @override
  Future<User> login({required String phone, required String password}) async {
    final response = await _client.post(
      AppConfig.apiUri('/auth/login'),
      body: <String, String>{
        'phone': phone.trim(),
        'password': password,
      },
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final user = User.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
      fallbackPhone: phone.trim(),
    );
    await _persistToken(user.accessToken);
    return user;
  }

  @override
  Future<User> register({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    final response = await _client.post(
      AppConfig.apiUri('/auth/register'),
      body: <String, String>{
        'phone': phone.trim(),
        'password': password,
        'name': name.trim(),
        'role': role,
      },
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final user = User.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
      fallbackPhone: phone.trim(),
    );
    await _persistToken(user.accessToken);
    return user;
  }

  @override
  Future<void> logout() async {
    try {
      await _secureStorage.delete(FlutterSecureStorageService.tokenKey);
    } on Object catch (e) {
      Logger.error('Error deleting token during logout: $e');
    }
  }

  @override
  Future<User?> restoreSession() async {
    Logger.startup('Session restoration initiated');
    try {
      final token = await _secureStorage.read(
        FlutterSecureStorageService.tokenKey,
      );
      if (token == null || token.isEmpty) {
        Logger.startup('No stored token found during session restoration');
        return null;
      }
      Logger.startup('Stored token found, verifying with /auth/me');

      // Use a short 3-second timeout for startup verification so physical devices
      // without backend access don't stall on splash screen.
      final response = await _client
          .get(AppConfig.apiUri('/auth/me'))
          .timeout(const Duration(seconds: 3));

      if (response.statusCode != HttpStatus.ok) {
        Logger.startup('Server rejected stored token (status: ${response.statusCode}), clearing session');
        await logout();
        return null;
      }

      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      final user = User.fromJson(data).copyWith(accessToken: token);
      Logger.startup('Session successfully restored for user ${user.id} (${user.phone})');
      return user;
    } on TimeoutException {
      Logger.startup('Session restoration network timeout - defaulting to offline/unauthenticated');
      return null;
    } on Object catch (e, st) {
      Logger.startup('Session restoration failed (${e.runtimeType}) - defaulting to unauthenticated');
      Logger.error('Session restore exception', error: e, stackTrace: st);
      return null;
    }
  }

  Future<void> _persistToken(String? token) async {
    if (token != null && token.isNotEmpty) {
      await _secureStorage.write(
        FlutterSecureStorageService.tokenKey,
        token,
      );
    }
  }
}
