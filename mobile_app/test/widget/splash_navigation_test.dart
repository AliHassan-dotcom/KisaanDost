import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/main.dart';
import 'package:kisaan_dost/models/user.dart';
import 'package:kisaan_dost/models/user_role.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/repositories/mock/mock_agri_stats_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_auth_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_dashboard_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_market_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_notification_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_pest_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_profile_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_satellite_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_scan_repository.dart';
import 'package:kisaan_dost/repositories/mock/mock_weather_repository.dart';
import 'package:kisaan_dost/screens/dashboard_screen.dart';

class _SuccessAuthRepo extends MockAuthRepository {
  @override
  Future<User?> restoreSession() async =>
      const User(id: 'u1', phone: '03001234567', role: UserRole.farmer);
}

class _EmptyAuthRepo extends MockAuthRepository {
  @override
  Future<User?> restoreSession() async => null;
}

class _ErrorAuthRepo extends MockAuthRepository {
  @override
  Future<User?> restoreSession() async =>
      throw TimeoutException('Backend connection timed out');
}

void main() {
  testWidgets('Splash exits to dashboard when session restoration succeeds', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(_SuccessAuthRepo()),
          dashboardRepositoryProvider.overrideWithValue(MockDashboardRepository()),
          weatherRepositoryProvider.overrideWithValue(MockWeatherRepository()),
          marketRepositoryProvider.overrideWithValue(MockMarketRepository()),
          pestRepositoryProvider.overrideWithValue(MockPestRepository()),
          satelliteRepositoryProvider.overrideWithValue(MockSatelliteRepository()),
          notificationRepositoryProvider.overrideWithValue(MockNotificationRepository()),
          agriStatsRepositoryProvider.overrideWithValue(MockAgriStatsRepository()),
          profileRepositoryProvider.overrideWithValue(MockProfileRepository()),
          scanRepositoryProvider.overrideWithValue(MockScanRepository()),
        ],
        child: const KisaanDostApp(),
      ),
    );

    // Initial frame shows splash
    expect(find.text('Kisaan Dost'), findsOneWidget);

    // Settle restoration and dashboard transition
    await tester.pumpAndSettle();

    // Successfully transitioned to dashboard
    expect(find.byType(DashboardScreen), findsOneWidget);
  });

  testWidgets('Splash exits to login when secure storage is empty', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(_EmptyAuthRepo()),
        ],
        child: const KisaanDostApp(),
      ),
    );

    // Initial frame shows splash
    expect(find.text('Kisaan Dost'), findsOneWidget);

    // Settle async restoration
    await tester.pumpAndSettle();

    // Successfully transitioned to login screen
    expect(find.text('Login'), findsWidgets);
    expect(find.text('Phone number'), findsOneWidget);
  });

  testWidgets('Splash exits gracefully to login when backend is unreachable', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(_ErrorAuthRepo()),
        ],
        child: const KisaanDostApp(),
      ),
    );

    // Initial frame shows splash
    expect(find.text('Kisaan Dost'), findsOneWidget);

    // Settle async restoration
    await tester.pumpAndSettle();

    // Unreachable backend cleanly defaults to login screen
    expect(find.text('Login'), findsWidgets);
    expect(find.text('Phone number'), findsOneWidget);
  });
}
