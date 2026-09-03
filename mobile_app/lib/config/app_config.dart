import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Environment-aware configuration and single source of truth for API base URL.
class AppConfig {
  const AppConfig._();

  static String _activeBaseUrl = 'http://192.168.1.5:8000';

  static String get apiBaseUrl {
    // 1. Check explicit runtime override
    if (_activeBaseUrl.isNotEmpty && _activeBaseUrl != 'http://192.168.1.5:8000') {
      return _activeBaseUrl;
    }

    // 2. Check dart-define
    const dartDefine = String.fromEnvironment('API_BASE_URL');
    if (dartDefine.isNotEmpty) return dartDefine;

    // 3. Check flutter_dotenv
    try {
      final envVal = dotenv.env['API_BASE_URL'];
      if (envVal != null && envVal.isNotEmpty) return envVal;
    } catch (_) {}

    return _activeBaseUrl;
  }

  static void setActiveBaseUrl(String url) {
    var cleaned = url.trim();
    if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
      cleaned = 'http://$cleaned';
    }
    if (cleaned.endsWith('/')) {
      cleaned = cleaned.substring(0, cleaned.length - 1);
    }
    _activeBaseUrl = cleaned;
  }

  static const String apiPrefix = '/api/v1';

  static Uri apiUri(String path) => Uri.parse('$apiBaseUrl$apiPrefix$path');

  /// Fallback candidates when network changes between USB tunnel, Wi-Fi, and emulator.
  static List<String> get candidateBaseUrls => <String>[
        apiBaseUrl,
        'http://192.168.1.5:8000',
        'http://192.168.1.7:8000',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://10.0.2.2:8000',
      ];

  /// Indicates if API_BASE_URL was explicitly provided at build/run time.
  static bool get isCustomBaseUrl => const bool.hasEnvironment('API_BASE_URL');

  /// Enforce HTTPS in release builds.
  static bool get requireHttps {
    const bool isRelease = bool.fromEnvironment('dart.vm.product');
    return isRelease;
  }

  /// Timeout for general HTTP requests.
  static Duration get httpTimeout => const Duration(seconds: 10);

  /// Validates security constraints for current build mode.
  static void validate() {
    if (requireHttps && !apiBaseUrl.startsWith('https://')) {
      throw StateError(
        'Release/production builds must use HTTPS. Configured API_BASE_URL ($apiBaseUrl) is insecure.',
      );
    }
  }
}
