/// Environment-aware configuration and single source of truth for API base URL.
///
/// Overridden at build/run time via:
///   `--dart-define=API_BASE_URL=http://<IP>:8000` (e.g. for physical devices)
///
/// Default:
///   `http://10.0.2.2:8000` (for Android emulator debug)
///
/// Production / Release builds enforce HTTPS.
class AppConfig {
  const AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String apiPrefix = '/api/v1';

  static Uri apiUri(String path) => Uri.parse('$apiBaseUrl$apiPrefix$path');

  /// Indicates if API_BASE_URL was explicitly provided at build/run time.
  static bool get isCustomBaseUrl => const bool.hasEnvironment('API_BASE_URL');

  /// Enforce HTTPS in release builds.
  static bool get requireHttps {
    const bool isRelease = bool.fromEnvironment('dart.vm.product');
    return isRelease;
  }

  /// Timeout for general HTTP requests.
  static Duration get httpTimeout => const Duration(seconds: 15);

  /// Validates security constraints for current build mode.
  static void validate() {
    if (requireHttps && !apiBaseUrl.startsWith('https://')) {
      throw StateError(
        'Release/production builds must use HTTPS. Configured API_BASE_URL ($apiBaseUrl) is insecure.',
      );
    }
  }
}
