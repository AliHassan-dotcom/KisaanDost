import '../../models/api_data_status.dart';
import '../../models/farm_health_summary.dart';
import '../../models/market_price.dart';
import '../../models/satellite_summary.dart';
import '../../models/weather_summary.dart';
import '../../repositories/dashboard_repository.dart';

class MockDashboardRepository implements DashboardRepository {
  MockDashboardRepository({this.delay = const Duration(milliseconds: 400)});

  final Duration delay;

  @override
  Future<DashboardData> getDashboard() async {
    await Future<void>.delayed(delay);
    return DashboardData(
      user: const <String, dynamic>{
        'user_id': 'user_000001',
        'role': 'farmer',
        'name': 'Test Farmer',
        'district': 'Lahore',
        'crop': 'wheat',
        'language': 'en',
      },
      weather: const WeatherSummary(
        district: 'Lahore',
        status: ApiDataStatus.mock,
        year: 2026,
        month: 9,
        temperatureC: 32.5,
        humidityPercent: 65.0,
        rainfallMm: 12.0,
      ),
      farmHealth: const FarmHealthSummary(
        status: 'no_recent_scan',
        confidence: null,
        uncertain: false,
        modelVersion: 'v2',
      ),
      market: const MarketPrice(
        crop: 'wheat',
        district: 'Lahore',
        status: ApiDataStatus.mock,
        currentPrice: 3200,
      ),
      satellite: const SatelliteSummary(
        district: 'Lahore',
        crop: 'wheat',
        status: ApiDataStatus.mock,
        reason: 'gee_not_connected',
      ),
      quickActions: const <Map<String, String>>[
        <String, String>{'label': 'Scan crop', 'href': '/scan', 'icon': 'camera'},
        <String, String>{'label': 'Weather', 'href': '/weather', 'icon': 'cloud'},
        <String, String>{'label': 'Pest alerts', 'href': '/pest', 'icon': 'alert'},
        <String, String>{'label': 'Market rates', 'href': '/market', 'icon': 'trend'},
      ],
    );
  }
}
