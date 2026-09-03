import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/user.dart';
import 'package:kisaan_dost/models/user_role.dart';
import 'package:kisaan_dost/providers/auth_provider.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/repositories/auth_repository.dart';

import '../helpers/test_container.dart';

class FakeAuthRepository implements AuthRepository {
  User? _user;
  bool throwOnLogin = false;

  @override
  Future<User> login({required String phone, required String password}) async {
    if (throwOnLogin) throw Exception('invalid');
    _user = User(
      id: 'user_001',
      phone: phone,
      role: UserRole.farmer,
      accessToken: 'tok',
    );
    return _user!;
  }

  @override
  Future<User> register({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    _user = User(id: 'user_002', phone: phone, role: UserRole.farmer);
    return _user!;
  }

  @override
  Future<void> logout() async => _user = null;

  @override
  Future<User?> restoreSession() async => _user;
}

void main() {
  group('AuthNotifier', () {
    test('logs in and updates state', () async {
      final repo = FakeAuthRepository();
      final container = createContainer(
        overrides: <Override>[
          authRepositoryProvider.overrideWithValue(repo),
        ],
      );

      await container.read(authProvider.notifier).login('03001001000', 'secret123');

      expect(container.read(authProvider).isAuthenticated, isTrue);
      expect(container.read(authProvider).user?.phone, '03001001000');
    });

    test('surfaces error on failed login', () async {
      final repo = FakeAuthRepository()..throwOnLogin = true;
      final container = createContainer(
        overrides: <Override>[
          authRepositoryProvider.overrideWithValue(repo),
        ],
      );

      await container.read(authProvider.notifier).login('03001001000', 'wrong');

      expect(container.read(authProvider).isAuthenticated, isFalse);
      expect(container.read(authProvider).error, isNotNull);
    });

    test('logout clears state', () async {
      final repo = FakeAuthRepository();
      final container = createContainer(
        overrides: <Override>[
          authRepositoryProvider.overrideWithValue(repo),
        ],
      );

      await container.read(authProvider.notifier).login('03001001000', 'secret123');
      await container.read(authProvider.notifier).logout();

      expect(container.read(authProvider).isAuthenticated, isFalse);
    });
  });
}
