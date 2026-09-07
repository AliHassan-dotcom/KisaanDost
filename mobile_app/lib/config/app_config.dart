import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Environment-aware configuration and single source of truth for API base URL.
class AppConfig {
  const AppConfig._();

  static String _activeBaseUrl = 'http://127.0.0.1:8000';

  static String get apiBaseUrl {
    // 1. Check explicit runtime override
    if (_activeBaseUrl.isNotEmpty && _activeBaseUrl != 'http://127.0.0.1:8000') {
      return _activeBaseUrl;
    }

    // 2. Check dart-define
    const dartDefine = String.fromEnvironment('API_BASE_URL');
    if (dartDefine.isNotEmpty) return dartDefine;

    // 3. Check flutter_dotenv
    try {
      final envVal = dotenv.env['API_BASE_URL'];
      if (envVal != null && envVal.isNotEmpty && !envVal.contains('your_')) {
        return envVal;
      }
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

  /// Fallback candidates prioritized by reachability:
  /// 1. 127.0.0.1:8000 (ADB reverse over USB - instant)
  /// 2. localhost:8000 (ADB reverse)
  /// 3. 192.168.1.9:8000 (Current Wi-Fi LAN)
  /// 4. 192.168.1.6:8000 / 192.168.1.5:8000 (LAN fallbacks)
  /// 5. 10.0.2.2:8000 (Android Emulator)
  static List<String> get candidateBaseUrls => <String>[
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'http://192.168.1.9:8000',
        'http://192.168.1.6:8000',
        'http://192.168.1.5:8000',
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
  static Duration get httpTimeout => const Duration(seconds: 4);

  /// Validates security constraints for current build mode.
  static void validate() {
    if (requireHttps && !apiBaseUrl.startsWith('https://')) {
      throw StateError(
        'Release/production builds must use HTTPS. Configured API_BASE_URL ($apiBaseUrl) is insecure.',
      );
    }
  }
}
