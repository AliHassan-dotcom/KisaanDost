import '../../models/api_data_status.dart';
import '../../models/farm_health_summary.dart';
import '../../models/market_price.dart';
import '../../models/risk_assessment.dart';
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
        'name': 'Farm Hero',
        'district': 'Multan',
        'crop': 'wheat',
        'language': 'en',
      },
      weather: const WeatherSummary(
        district: 'Multan',
        status: ApiDataStatus.mock,
        year: 2026,
        month: 9,
        temperatureC: 32.5,
        humidityPercent: 65.0,
        rainfallMm: 12.0,
      ),
      farmHealth: const FarmHealthSummary(
        status: 'Wheat (گندم) - Leaf Rust Detected',
        confidence: 0.92,
        uncertain: false,
        modelVersion: 'PyTorch CNN v2.0',
      ),
      market: const MarketPrice(
        crop: 'wheat',
        district: 'Lahore',
        status: ApiDataStatus.mock,
        currentPrice: 3850,
      ),
      satellite: const SatelliteSummary(
        district: 'Multan',
        crop: 'wheat',
        status: ApiDataStatus.mock,
        ndvi: 0.685,
        reason: 'good_vegetation',
      ),
      riskAssessment: RiskAssessment.mockDefault(),
      quickActions: const <Map<String, String>>[
        <String, String>{'label': 'Urdu Voice', 'href': '/voice', 'icon': 'mic'},
        <String, String>{'label': 'Scan crop', 'href': '/scan', 'icon': 'camera'},
        <String, String>{'label': 'Weather', 'href': '/weather', 'icon': 'cloud'},
        <String, String>{'label': 'Pest alerts', 'href': '/pest', 'icon': 'alert'},
        <String, String>{'label': 'Market rates', 'href': '/market', 'icon': 'trend'},
      ],
    );
  }
}
