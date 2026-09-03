import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:http/http.dart';

import '../config/app_config.dart';
import 'secure_storage_service.dart';

class UnauthorizedException implements Exception {
  const UnauthorizedException(this.message);
  final String message;

  @override
  String toString() => message;
}

class HttpClient {
  HttpClient({
    required this._secureStorage,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final SecureStorageService _secureStorage;
  final http.Client _client;

  Future<Map<String, String>> _headers({bool multipart = false}) async {
    final headers = <String, String>{
      'Accept': 'application/json',
      if (!multipart) 'Content-Type': 'application/json',
    };
    final token = await _secureStorage.read(
      FlutterSecureStorageService.tokenKey,
    );
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<T> _withFallback<T>(Future<T> Function(Uri uri) requestFn, Uri initialUri) async {
    try {
      return await requestFn(initialUri);
    } catch (e) {
      // If the primary connection failed (e.g. SocketException), test candidates
      for (final candidateBase in AppConfig.candidateBaseUrls) {
        final candidateUri = _replaceBase(initialUri, candidateBase);
        if (candidateUri == initialUri) continue;
        try {
          final result = await requestFn(candidateUri);
          AppConfig.setActiveBaseUrl(candidateBase);
          return result;
        } catch (_) {
          continue;
        }
      }
      rethrow;
    }
  }

  Uri _replaceBase(Uri uri, String newBase) {
    final parsedBase = Uri.parse(newBase);
    return uri.replace(
      scheme: parsedBase.scheme,
      host: parsedBase.host,
      port: parsedBase.hasPort ? parsedBase.port : null,
    );
  }

  Future<Response> get(Uri uri) async {
    return _withFallback((targetUri) async {
      final response = await _client
          .get(targetUri, headers: await _headers())
          .timeout(AppConfig.httpTimeout);
      return _checkStatus(response);
    }, uri);
  }

  Future<Response> post(Uri uri, {Object? body}) async {
    return _withFallback((targetUri) async {
      final response = await _client
          .post(
            targetUri,
            headers: await _headers(),
            body: body == null ? null : jsonEncode(body),
          )
          .timeout(AppConfig.httpTimeout);
      return _checkStatus(response);
    }, uri);
  }

  Future<Response> put(Uri uri, {Object? body}) async {
    return _withFallback((targetUri) async {
      final response = await _client
          .put(
            targetUri,
            headers: await _headers(),
            body: body == null ? null : jsonEncode(body),
          )
          .timeout(AppConfig.httpTimeout);
      return _checkStatus(response);
    }, uri);
  }

  Future<Response> patch(Uri uri, {Object? body}) async {
    return _withFallback((targetUri) async {
      final response = await _client
          .patch(
            targetUri,
            headers: await _headers(),
            body: body == null ? null : jsonEncode(body),
          )
          .timeout(AppConfig.httpTimeout);
      return _checkStatus(response);
    }, uri);
  }

  Future<StreamedResponse> multipartPost(
    Uri uri, {
    required Map<String, String> fields,
    required List<MultipartFile> files,
  }) async {
    return _withFallback((targetUri) async {
      final request = http.MultipartRequest('POST', targetUri)
        ..fields.addAll(fields)
        ..files.addAll(files)
        ..headers.addAll(await _headers(multipart: true));

      final response = await request.send().timeout(AppConfig.httpTimeout);
      if (response.statusCode == HttpStatus.unauthorized) {
        throw const UnauthorizedException('Session expired. Please log in again.');
      }
      return response;
    }, uri);
  }

  Response _checkStatus(Response response) {
    if (response.statusCode == HttpStatus.unauthorized) {
      throw const UnauthorizedException('Session expired. Please log in again.');
    }
    return response;
  }
}
