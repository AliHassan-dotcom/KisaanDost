import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/user.dart';
import 'package:kisaan_dost/models/user_role.dart';

void main() {
  group('UserRole', () {
    test('farmer is not admin', () {
      expect(UserRole.farmer.isAdmin, isFalse);
    });

    test('admin is admin', () {
      expect(UserRole.admin.isAdmin, isTrue);
    });

    test('extension worker serializes correctly', () {
      expect(UserRole.extensionWorker.toJson(), 'extension_worker');
      expect(UserRole.fromJson('extension_worker'), UserRole.extensionWorker);
    });

    test('unknown role throws', () {
      expect(() => UserRole.fromJson('unknown'), throwsFormatException);
    });
  });

  group('User', () {
    test('copyWith preserves fields', () {
      const user = User(id: '1', phone: '0300', role: UserRole.farmer);
      final updated = user.copyWith(accessToken: 'abc');
      expect(updated.accessToken, 'abc');
      expect(updated.phone, user.phone);
    });
  });
}
