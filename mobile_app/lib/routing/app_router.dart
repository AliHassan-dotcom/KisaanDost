import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/user_role.dart';
import '../providers/auth_provider.dart';
import '../screens/admin_placeholder_screen.dart';
import '../screens/dashboard_screen.dart';
import '../screens/irrigation_screen.dart';
import '../screens/login_screen.dart';
import '../screens/market_screen.dart';
import '../screens/pest_alerts_screen.dart';
import '../screens/profile_setup_screen.dart';
import '../screens/register_screen.dart';
import '../screens/satellite_screen.dart';
import '../screens/scan_screen.dart';
import '../screens/settings_screen.dart';
import '../screens/splash_screen.dart';
import '../screens/weather_screen.dart';
import '../utils/logger.dart';

class AppRoutes {
  const AppRoutes._();

  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String dashboard = '/dashboard';
  static const String profile = '/profile';
  static const String scan = '/scan';
  static const String weather = '/weather';
  static const String irrigation = '/irrigation';
  static const String pest = '/pest';
  static const String satellite = '/satellite';
  static const String market = '/market';
  static const String settings = '/settings';
  static const String admin = '/admin';
}

class RouterNotifier extends ChangeNotifier {
  RouterNotifier(this._ref) {
    _ref.listen<AuthState>(
      authProvider,
      (previous, next) {
        Logger.startup(
          'RouterNotifier received auth change',
          'initialized=${next.isInitialized}, loading=${next.isLoading}, auth=${next.isAuthenticated}',
        );
        notifyListeners();
      },
    );
  }

  final Ref _ref;

  String? redirect(BuildContext context, GoRouterState state) {
    final auth = _ref.read(authProvider);
    final isAuthenticated = auth.isAuthenticated;
    final isInitialized = auth.isInitialized;
    final location = state.matchedLocation;

    final isAuthRoute = location == AppRoutes.login ||
        location == AppRoutes.register ||
        location == AppRoutes.splash;

    Logger.startup(
      'Router redirect evaluation',
      'location=$location, isInitialized=$isInitialized, isAuth=$isAuthenticated',
    );

    // If currently on splash screen:
    if (location == AppRoutes.splash) {
      if (!isInitialized) return null;
      final target = isAuthenticated ? AppRoutes.dashboard : AppRoutes.login;
      Logger.startup('Splash redirect resolved -> $target');
      return target;
    }

    if (!isInitialized) return null;

    if (!isAuthenticated && !isAuthRoute) {
      Logger.startup('Unauthenticated user redirected -> ${AppRoutes.login}');
      return AppRoutes.login;
    }

    if (isAuthenticated && (location == AppRoutes.login || location == AppRoutes.register)) {
      Logger.startup('Authenticated user redirected -> ${AppRoutes.dashboard}');
      return AppRoutes.dashboard;
    }

    // Admin guard.
    if (location == AppRoutes.admin && auth.user?.role != UserRole.admin) {
      Logger.startup('Non-admin user redirected from admin -> ${AppRoutes.dashboard}');
      return AppRoutes.dashboard;
    }

    return null;
  }
}

final routerNotifierProvider = Provider<RouterNotifier>((ref) => RouterNotifier(ref));

final appRouterProvider = Provider<GoRouter>((ref) {
  final notifier = ref.watch(routerNotifierProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: notifier,
    redirect: notifier.redirect,
    routes: <RouteBase>[
      GoRoute(
        path: AppRoutes.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoutes.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: AppRoutes.dashboard,
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: AppRoutes.profile,
        builder: (context, state) => const ProfileSetupScreen(),
      ),
      GoRoute(
        path: AppRoutes.scan,
        builder: (context, state) => const ScanScreen(),
      ),
      GoRoute(
        path: AppRoutes.weather,
        builder: (context, state) => const WeatherScreen(),
      ),
      GoRoute(
        path: AppRoutes.irrigation,
        builder: (context, state) => const IrrigationScreen(),
      ),
      GoRoute(
        path: AppRoutes.pest,
        builder: (context, state) => const PestAlertsScreen(),
      ),
      GoRoute(
        path: AppRoutes.satellite,
        builder: (context, state) => const SatelliteScreen(),
      ),
      GoRoute(
        path: AppRoutes.market,
        builder: (context, state) => const MarketScreen(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: AppRoutes.admin,
        builder: (context, state) => const AdminPlaceholderScreen(),
      ),
    ],
  );
});
