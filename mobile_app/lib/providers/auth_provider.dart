import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/user.dart';
import '../repositories/auth_repository.dart';
import '../utils/error_mapper.dart';
import '../utils/logger.dart';
import 'dependency_providers.dart';

class AuthState {
  const AuthState({
    this.user,
    this.isLoading = false,
    this.isInitialized = false,
    this.error,
  });

  final User? user;
  final bool isLoading;
  final bool isInitialized;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    User? user,
    bool? isLoading,
    bool? isInitialized,
    String? error,
  }) =>
      AuthState(
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        isInitialized: isInitialized ?? this.isInitialized,
        error: error ?? this.error,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._repository) : super(const AuthState());

  final AuthRepository _repository;

  Future<void> restoreSession() async {
    Logger.startup('AuthNotifier.restoreSession starting');
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _repository.restoreSession();
      state = AuthState(
        user: user,
        isLoading: false,
        isInitialized: true,
      );
      Logger.startup(
        'AuthNotifier.restoreSession completed',
        'authenticated=${user != null}, isInitialized=true',
      );
    } on Object catch (e, st) {
      Logger.error('AuthNotifier.restoreSession caught error', error: e, stackTrace: st);
      state = AuthState(
        error: ApiException.userMessage(e),
        isLoading: false,
        isInitialized: true,
      );
    }
  }

  Future<void> login(String phone, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _repository.login(phone: phone, password: password);
      state = AuthState(
        user: user,
        isLoading: false,
        isInitialized: true,
      );
    } on Object catch (e) {
      state = AuthState(
        error: ApiException.userMessage(e),
        isLoading: false,
        isInitialized: true,
      );
    }
  }

  Future<void> register({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _repository.register(
        phone: phone,
        password: password,
        name: name,
        role: role,
      );
      state = AuthState(
        user: user,
        isLoading: false,
        isInitialized: true,
      );
    } on Object catch (e) {
      state = AuthState(
        error: ApiException.userMessage(e),
        isLoading: false,
        isInitialized: true,
      );
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AuthState(isInitialized: true);
  }

  void clearError() => state = state.copyWith(error: null);
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(authRepositoryProvider)),
);
