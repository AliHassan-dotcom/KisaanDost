import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/secure_storage_service.dart';
import 'dependency_providers.dart';

class SettingsState {
  const SettingsState({
    this.language = 'en',
    this.notificationsEnabled = true,
    this.darkMode = false,
  });

  final String language;
  final bool notificationsEnabled;
  final bool darkMode;

  SettingsState copyWith({
    String? language,
    bool? notificationsEnabled,
    bool? darkMode,
  }) =>
      SettingsState(
        language: language ?? this.language,
        notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
        darkMode: darkMode ?? this.darkMode,
      );
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier(this._secureStorage) : super(const SettingsState()) {
    _loadLanguage();
  }

  final SecureStorageService _secureStorage;

  Future<void> _loadLanguage() async {
    final lang = await _secureStorage.read(
      FlutterSecureStorageService.languageKey,
    );
    if (lang != null) {
      state = state.copyWith(language: lang);
    }
  }

  Future<void> setLanguage(String language) async {
    await _secureStorage.write(
      FlutterSecureStorageService.languageKey,
      language,
    );
    state = state.copyWith(language: language);
  }

  void setNotifications(bool enabled) {
    state = state.copyWith(notificationsEnabled: enabled);
  }

  void setDarkMode(bool enabled) {
    state = state.copyWith(darkMode: enabled);
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>(
  (ref) => SettingsNotifier(ref.watch(secureStorageProvider)),
);
