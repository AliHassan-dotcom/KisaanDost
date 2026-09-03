import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'config/app_config.dart';
import 'routing/app_router.dart';
import 'utils/logger.dart';

void main() {
  Logger.startup('App bootstrap initiated');
  WidgetsFlutterBinding.ensureInitialized();
  Logger.startup('WidgetsFlutterBinding initialized');
  runApp(const ProviderScope(child: KisaanDostApp()));
  Logger.startup('runApp executed');
}

class KisaanDostApp extends ConsumerWidget {
  const KisaanDostApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Kisaan Dost',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.green,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      supportedLocales: const <Locale>[
        Locale('en'),
        Locale('ur'),
      ],
      routerConfig: router,
      // Enforce HTTPS in release builds by asserting the base URL is secure.
      builder: (context, child) {
        assert(
          !AppConfig.requireHttps || AppConfig.apiBaseUrl.startsWith('https'),
          'Release builds must use HTTPS',
        );
        return child ?? const SizedBox.shrink();
      },
    );
  }
}
