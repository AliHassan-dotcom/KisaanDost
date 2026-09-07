import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/config/env_config.dart';

void main() {
  group('EnvConfig Unit Tests', () {
    tearDown(() {
      EnvConfig.resetOverrides();
    });

    test('EnvConfig returns defaults or empty string when unconfigured', () {
      expect(EnvConfig.openweathermapApiKey, isNotNull);
      expect(EnvConfig.faoApiKey, isNotNull);
      expect(EnvConfig.pakistanDataApiKey, isNotNull);
      expect(EnvConfig.nasaApiKey, isNotNull);
      expect(EnvConfig.cabiApiKey, isNotNull);
      expect(EnvConfig.googleApiKey, isNotNull);
      expect(EnvConfig.googleSearchEngineId, isNotNull);
    });

    test('EnvConfig respects runtime testing overrides', () {
      EnvConfig.setOverrides(
        openweathermapApiKey: 'test_owm_key',
        faoApiKey: 'test_fao_key',
        pakistanDataApiKey: 'test_pak_key',
        nasaApiKey: 'test_nasa_key',
        cabiApiKey: 'test_cabi_key',
        googleApiKey: 'test_google_key',
        googleSearchEngineId: 'test_search_engine_id',
      );

      expect(EnvConfig.openweathermapApiKey, equals('test_owm_key'));
      expect(EnvConfig.faoApiKey, equals('test_fao_key'));
      expect(EnvConfig.pakistanDataApiKey, equals('test_pak_key'));
      expect(EnvConfig.nasaApiKey, equals('test_nasa_key'));
      expect(EnvConfig.cabiApiKey, equals('test_cabi_key'));
      expect(EnvConfig.googleApiKey, equals('test_google_key'));
      expect(EnvConfig.googleSearchEngineId, equals('test_search_engine_id'));

      EnvConfig.resetOverrides();
      expect(EnvConfig.openweathermapApiKey, isNot(equals('test_owm_key')));
    });
  });
}
