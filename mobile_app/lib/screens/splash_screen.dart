import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../routing/app_router.dart';
import '../utils/logger.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Logger.startup('SplashScreen mounted');

    // Kick off session restore on next microtask.
    Future<void>.microtask(() async {
      if (!mounted) return;
      Logger.startup('SplashScreen invoking restoreSession');
      await ref.read(authProvider.notifier).restoreSession();
    });
  }

  void _navigate(AuthState auth) {
    if (!mounted) return;
    final destination = auth.isAuthenticated ? AppRoutes.dashboard : AppRoutes.login;
    Logger.startup('SplashScreen navigating to $destination');
    context.go(destination);
  }

  @override
  Widget build(BuildContext context) {
    // Listen to auth changes and navigate as soon as initialization completes.
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.isInitialized && !next.isLoading) {
        _navigate(next);
      }
    });

    final auth = ref.watch(authProvider);

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const FlutterLogo(size: 96),
              const SizedBox(height: 24),
              const Text(
                'Kisaan Dost',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                'Your Digital Farming Companion',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 24),
              if (!auth.isInitialized || auth.isLoading) ...[
                const CircularProgressIndicator(),
                const SizedBox(height: 16),
                Text(
                  'Starting up...',
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
                ),
              ],
              if (auth.error != null) ...[
                Text(
                  auth.error!,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => context.go(AppRoutes.login),
                  child: const Text('Continue to Login'),
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () {
                    ref.read(authProvider.notifier).restoreSession();
                  },
                  child: const Text('Retry Connection'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
