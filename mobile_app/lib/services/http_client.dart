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

  Future<Response> get(Uri uri) async {
    final response = await _client
        .get(uri, headers: await _headers())
        .timeout(AppConfig.httpTimeout);
    return _checkStatus(response);
  }

  Future<Response> post(Uri uri, {Object? body}) async {
    final response = await _client
        .post(
          uri,
          headers: await _headers(),
          body: body == null ? null : jsonEncode(body),
        )
        .timeout(AppConfig.httpTimeout);
    return _checkStatus(response);
  }

  Future<Response> put(Uri uri, {Object? body}) async {
    final response = await _client
        .put(
          uri,
          headers: await _headers(),
          body: body == null ? null : jsonEncode(body),
        )
        .timeout(AppConfig.httpTimeout);
    return _checkStatus(response);
  }

  Future<Response> patch(Uri uri, {Object? body}) async {
    final response = await _client
        .patch(
          uri,
          headers: await _headers(),
          body: body == null ? null : jsonEncode(body),
        )
        .timeout(AppConfig.httpTimeout);
    return _checkStatus(response);
  }

  Future<StreamedResponse> multipartPost(
    Uri uri, {
    required Map<String, String> fields,
    required List<MultipartFile> files,
  }) async {
    final request = http.MultipartRequest('POST', uri)
      ..fields.addAll(fields)
      ..files.addAll(files)
      ..headers.addAll(await _headers(multipart: true));

    final response = await request.send().timeout(AppConfig.httpTimeout);
    if (response.statusCode == HttpStatus.unauthorized) {
      throw const UnauthorizedException('Session expired. Please log in again.');
    }
    return response;
  }

  Response _checkStatus(Response response) {
    if (response.statusCode == HttpStatus.unauthorized) {
      throw const UnauthorizedException('Session expired. Please log in again.');
    }
    return response;
  }
}
