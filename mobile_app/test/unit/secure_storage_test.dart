import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/secure_storage_service.dart';

import '../mocks/mock_secure_storage.dart';

void main() {
  group('SecureStorageService', () {
    late MockSecureStorage storage;

    setUp(() => storage = MockSecureStorage());

    test('write and read token', () async {
      await storage.write(FlutterSecureStorageService.tokenKey, 'token_123');
      expect(await storage.read(FlutterSecureStorageService.tokenKey), 'token_123');
    });

    test('delete removes value', () async {
      await storage.write('key', 'value');
      await storage.delete('key');
      expect(await storage.read('key'), isNull);
    });

    test('deleteAll clears store', () async {
      await storage.write('a', '1');
      await storage.write('b', '2');
      await storage.deleteAll();
      expect(await storage.read('a'), isNull);
      expect(await storage.read('b'), isNull);
    });
  });
}
