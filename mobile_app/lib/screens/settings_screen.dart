import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../providers/settings_provider.dart';
import '../routing/app_router.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/language_toggle.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      appBar: const KdAppBar(title: 'Settings'),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              'Language',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            LanguageToggle(
              language: settings.language,
              onChanged: (lang) =>
                  ref.read(settingsProvider.notifier).setLanguage(lang),
            ),
            const SizedBox(height: 24),
            SwitchListTile(
              title: const Text('Notifications'),
              value: settings.notificationsEnabled,
              onChanged: (value) =>
                  ref.read(settingsProvider.notifier).setNotifications(value),
            ),
            SwitchListTile(
              title: const Text('Dark mode'),
              value: settings.darkMode,
              onChanged: (value) =>
                  ref.read(settingsProvider.notifier).setDarkMode(value),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () async {
                await ref.read(authProvider.notifier).logout();
                if (context.mounted) context.go(AppRoutes.login);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
              ),
              child: const Text('Logout'),
            ),
          ],
        ),
      ),
    );
  }
}
