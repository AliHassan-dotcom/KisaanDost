import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../repositories/auth_repository.dart';
import '../repositories/auth_repository_impl.dart';
import '../repositories/dashboard_repository.dart';
import '../repositories/dashboard_repository_impl.dart';
import '../repositories/market_repository.dart';
import '../repositories/market_repository_impl.dart';
import '../repositories/mock/mock_auth_repository.dart';
import '../repositories/mock/mock_dashboard_repository.dart';
import '../repositories/mock/mock_market_repository.dart';
import '../repositories/mock/mock_pest_repository.dart';
import '../repositories/mock/mock_profile_repository.dart';
import '../repositories/mock/mock_satellite_repository.dart';
import '../repositories/mock/mock_scan_repository.dart';
import '../repositories/mock/mock_weather_repository.dart';
import '../repositories/agri_stats_repository.dart';
import '../repositories/agri_stats_repository_impl.dart';
import '../repositories/mock/mock_agri_stats_repository.dart';
import '../repositories/mock/mock_notification_repository.dart';
import '../repositories/notification_repository.dart';
import '../repositories/notification_repository_impl.dart';
import '../repositories/pest_repository.dart';
import '../repositories/pest_repository_impl.dart';
import '../repositories/profile_repository.dart';
import '../repositories/profile_repository_impl.dart';
import '../repositories/satellite_repository.dart';
import '../repositories/satellite_repository_impl.dart';
import '../repositories/scan_repository.dart';
import '../repositories/scan_repository_impl.dart';
import '../repositories/weather_repository.dart';
import '../repositories/weather_repository_impl.dart';
import '../services/http_client.dart';
import '../services/secure_storage_service.dart';

/// Toggle for offline development. When true, all repositories return mock data.
const bool useMocks = bool.fromEnvironment('USE_MOCKS', defaultValue: false);

final secureStorageProvider = Provider<SecureStorageService>(
  (ref) => const FlutterSecureStorageService(),
);

final httpClientProvider = Provider<HttpClient>(
  (ref) => HttpClient(
    secureStorage: ref.watch(secureStorageProvider),
  ),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => useMocks
      ? MockAuthRepository()
      : AuthRepositoryImpl(
          client: ref.watch(httpClientProvider),
          secureStorage: ref.watch(secureStorageProvider),
        ),
);

final profileRepositoryProvider = Provider<ProfileRepository>(
  (ref) => useMocks
      ? MockProfileRepository()
      : ProfileRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final dashboardRepositoryProvider = Provider<DashboardRepository>(
  (ref) => useMocks
      ? MockDashboardRepository()
      : DashboardRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final weatherRepositoryProvider = Provider<WeatherRepository>(
  (ref) => useMocks
      ? MockWeatherRepository()
      : WeatherRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final scanRepositoryProvider = Provider<ScanRepository>(
  (ref) => useMocks
      ? MockScanRepository()
      : ScanRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final marketRepositoryProvider = Provider<MarketRepository>(
  (ref) => useMocks
      ? MockMarketRepository()
      : MarketRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final satelliteRepositoryProvider = Provider<SatelliteRepository>(
  (ref) => useMocks
      ? MockSatelliteRepository()
      : SatelliteRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final pestRepositoryProvider = Provider<PestRepository>(
  (ref) => useMocks
      ? MockPestRepository()
      : PestRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final agriStatsRepositoryProvider = Provider<AgriStatsRepository>(
  (ref) => useMocks
      ? MockAgriStatsRepository()
      : AgriStatsRepositoryImpl(client: ref.watch(httpClientProvider)),
);

final notificationRepositoryProvider = Provider<NotificationRepository>(
  (ref) => useMocks
      ? MockNotificationRepository()
      : NotificationRepositoryImpl(client: ref.watch(httpClientProvider)),
);


