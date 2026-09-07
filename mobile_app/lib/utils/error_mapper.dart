import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart';

import '../config/app_config.dart';

class ApiException implements Exception {
  const ApiException({
    required this.statusCode,
    required this.message,
    this.body,
  });

  final int statusCode;
  final String message;
  final String? body;

  factory ApiException.fromResponse(Response response) {
    String message;
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      message = (decoded['detail'] as String?) ??
          (decoded['message'] as String?) ??
          response.reasonPhrase ??
          'Request failed';
    } on FormatException catch (_) {
      message = response.reasonPhrase ?? 'Request failed';
    }
    return ApiException(
      statusCode: response.statusCode,
      message: message,
      body: response.body,
    );
  }

  static String userMessage(Object error) {
    if (error is ApiException) {
      switch (error.statusCode) {
        case HttpStatus.unauthorized:
          return 'Invalid phone or password.';
        case HttpStatus.conflict:
          return 'This phone number is already registered.';
        case HttpStatus.badRequest:
          return 'Please check your input and try again.';
        case HttpStatus.notFound:
          return 'Requested resource not found.';
        case HttpStatus.serviceUnavailable:
          return 'Service is temporarily unavailable. Please try again later.';
        default:
          return error.message.isNotEmpty ? error.message : 'Something went wrong. Please try again.';
      }
    }
    if (error is TimeoutException) {
      return 'Connection timed out reaching ${AppConfig.apiBaseUrl}. Please check network or server status.';
    }
    if (error is SocketException) {
      return 'Cannot reach server at ${AppConfig.apiBaseUrl}. Please ensure FastAPI backend is running and your device is on the same network.';
    }
    if (error is ClientException) {
      return 'Network connection error reaching ${AppConfig.apiBaseUrl}. Please check Wi-Fi connection.';
    }
    if (error is HttpException || error is HandshakeException) {
      return 'Communication error with server at ${AppConfig.apiBaseUrl}.';
    }
    if (error.runtimeType.toString() == 'UnauthorizedException') {
      return 'Invalid phone or password.';
    }
    return 'Connection failed. Please check network and server status.';
  }

  @override
  String toString() => 'ApiException($statusCode): $message';
}
