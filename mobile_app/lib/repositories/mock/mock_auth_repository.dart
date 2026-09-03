import '../../models/user.dart';
import '../../models/user_role.dart';
import '../../repositories/auth_repository.dart';

class MockAuthRepository implements AuthRepository {
  MockAuthRepository({this.delay = const Duration(milliseconds: 300)});

  final Duration delay;
  User? _currentUser;

  @override
  Future<User> login({required String phone, required String password}) async {
    await Future<void>.delayed(delay);
    if (password != 'secret123') {
      throw Exception('Invalid credentials');
    }
    final user = User(
      id: 'user_000001',
      phone: phone,
      role: UserRole.farmer,
      accessToken: 'mock_token',
    );
    _currentUser = user;
    return user;
  }

  @override
  Future<User> register({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    await Future<void>.delayed(delay);
    final user = User(
      id: 'user_000002',
      phone: phone,
      role: UserRole.fromJson(role),
      accessToken: 'mock_token',
    );
    _currentUser = user;
    return user;
  }

  @override
  Future<void> logout() async {
    _currentUser = null;
  }

  @override
  Future<User?> restoreSession() async {
    await Future<void>.delayed(delay);
    return _currentUser;
  }
}
