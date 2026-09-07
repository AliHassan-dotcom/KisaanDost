import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Centralized configuration provider for external public dataset and AI API keys.
/// Prioritizes --dart-define environment variables, then flutter_dotenv (.env file).
class EnvConfig {
  const EnvConfig._();

  // Runtime overrides for testing
  static String? _overrideOpenweathermapApiKey;
  static String? _overrideFaoApiKey;
  static String? _overridePakistanDataApiKey;
  static String? _overrideNasaApiKey;
  static String? _overrideCabiApiKey;
  static String? _overrideGoogleApiKey;
  static String? _overrideGoogleSearchEngineId;

  static String _readKey(String envName, String? overrideVal) {
    if (overrideVal != null) return overrideVal;

    // 1. Check dart-define
    final fromEnv = String.fromEnvironment(envName);
    if (fromEnv.isNotEmpty) return fromEnv;

    // 2. Check flutter_dotenv (.env)
    try {
      final val = dotenv.env[envName];
      if (val != null && val.isNotEmpty && !val.contains('your_')) {
        return val;
      }
    } catch (_) {}

    return '';
  }

  static String get openweathermapApiKey =>
      _readKey('OPENWEATHERMAP_API_KEY', _overrideOpenweathermapApiKey);

  static String get faoApiKey =>
      _readKey('FAO_API_KEY', _overrideFaoApiKey);

  static String get pakistanDataApiKey =>
      _readKey('PAKISTAN_DATA_API_KEY', _overridePakistanDataApiKey);

  static String get nasaApiKey =>
      _readKey('NASA_EARTHDATA_API_KEY', _overrideNasaApiKey);

  static String get cabiApiKey =>
      _readKey('CABI_API_KEY', _overrideCabiApiKey);

  static String get googleApiKey =>
      _readKey('GOOGLE_API_KEY', _overrideGoogleApiKey);

  static String get googleSearchEngineId =>
      _readKey('GOOGLE_SEARCH_ENGINE_ID', _overrideGoogleSearchEngineId);

  // Test helpers to inject keys during testing
  static void setOverrides({
    String? openweathermapApiKey,
    String? faoApiKey,
    String? pakistanDataApiKey,
    String? nasaApiKey,
    String? cabiApiKey,
    String? googleApiKey,
    String? googleSearchEngineId,
  }) {
    _overrideOpenweathermapApiKey = openweathermapApiKey;
    _overrideFaoApiKey = faoApiKey;
    _overridePakistanDataApiKey = pakistanDataApiKey;
    _overrideNasaApiKey = nasaApiKey;
    _overrideCabiApiKey = cabiApiKey;
    _overrideGoogleApiKey = googleApiKey;
    _overrideGoogleSearchEngineId = googleSearchEngineId;
  }

  static void resetOverrides() {
    _overrideOpenweathermapApiKey = null;
    _overrideFaoApiKey = null;
    _overridePakistanDataApiKey = null;
    _overrideNasaApiKey = null;
    _overrideCabiApiKey = null;
    _overrideGoogleApiKey = null;
    _overrideGoogleSearchEngineId = null;
  }
}
