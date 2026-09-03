import '../models/user.dart';

abstract interface class AuthRepository {
  Future<User> login({required String phone, required String password});
  Future<User> register({
    required String phone,
    required String password,
    required String name,
    required String role,
  });
  Future<void> logout();
  Future<User?> restoreSession();
}
