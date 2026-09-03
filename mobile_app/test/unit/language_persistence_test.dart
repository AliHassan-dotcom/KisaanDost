import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/providers/settings_provider.dart';
import 'package:kisaan_dost/services/secure_storage_service.dart';

import '../helpers/test_container.dart';
import '../mocks/mock_secure_storage.dart';

void main() {
  group('SettingsNotifier', () {
    test('loads persisted language on creation', () async {
      final storage = MockSecureStorage();
      await storage.write(FlutterSecureStorageService.languageKey, 'ur');

      final container = createContainer(
        overrides: <Override>[
          secureStorageProvider.overrideWithValue(storage),
        ],
      );

      // Keep a listener so Riverpod propagates the async state update.
      container.listen(settingsProvider, (previous, next) {});
      await pumpEventQueue();

      expect(container.read(settingsProvider).language, 'ur');
    });

    test('setLanguage persists and updates state', () async {
      final storage = MockSecureStorage();
      final container = createContainer(
        overrides: <Override>[
          secureStorageProvider.overrideWithValue(storage),
        ],
      );

      await container.read(settingsProvider.notifier).setLanguage('ur');

      expect(container.read(settingsProvider).language, 'ur');
      expect(
        await storage.read(FlutterSecureStorageService.languageKey),
        'ur',
      );
    });
  });
}
