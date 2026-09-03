import 'dart:developer' as developer;
import 'package:flutter/foundation.dart';

class Logger {
  const Logger._();

  static void info(String message) {
    if (kDebugMode) {
      debugPrint('[KisaanDost] $message');
    }
    developer.log(message, name: 'KisaanDost');
  }

  static void startup(String stage, [String? details]) {
    final msg = details != null ? '[STARTUP] $stage: $details' : '[STARTUP] $stage';
    if (kDebugMode) {
      debugPrint(msg);
    }
    developer.log(msg, name: 'KisaanDost.Startup');
  }

  static void error(String message, {Object? error, StackTrace? stackTrace}) {
    if (kDebugMode) {
      debugPrint('[KisaanDost ERROR] $message${error != null ? ": $error" : ""}');
    }
    developer.log(
      message,
      name: 'KisaanDost',
      error: error,
      stackTrace: stackTrace,
    );
  }
}
